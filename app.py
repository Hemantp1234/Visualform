from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, init_db, derive_master_key
from aws_services import AWSManager, validate_aws_credentials
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///visualform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Validation
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('register'))
        
        if password != password_confirm:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(username=username)
        user.set_password(password)
        
        # Generate and store salt for key derivation
        _, salt = derive_master_key(username, password)
        user.key_derivation_salt = salt
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/credentials', methods=['GET', 'POST'])
@login_required
def manage_credentials():
    if request.method == 'POST':
        access_key = request.form.get('access_key')
        secret_key = request.form.get('secret_key')
        region = request.form.get('region', 'us-east-1')
        
        # Validate credentials
        validation = validate_aws_credentials(access_key, secret_key, region)
        
        if not validation['valid']:
            flash(f"Invalid credentials: {validation['message']}", 'error')
            return redirect(url_for('manage_credentials'))
        
        # Store encrypted credentials
        current_user.set_aws_credentials(access_key, secret_key, region, current_user.password_hash)
        db.session.commit()
        
        flash('AWS credentials saved successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('credentials.html')


@app.route('/dashboard')
@login_required
def dashboard():
    # Check if user has credentials
    creds = current_user.get_aws_credentials(current_user.password_hash)
    
    if not creds:
        flash('Please configure AWS credentials first', 'warning')
        return redirect(url_for('manage_credentials'))
    
    # Get all instances
    try:
        manager = AWSManager(creds['access_key'], creds['secret_key'], creds['region'])
        instances = manager.get_all_instances()
    except Exception as e:
        flash(f'Error fetching instances: {str(e)}', 'error')
        instances = []
    
    return render_template('dashboard.html', instances=instances)


@app.route('/launch-form')
@login_required
def launch_form():
    creds = current_user.get_aws_credentials(current_user.password_hash)
    
    if not creds:
        flash('Please configure AWS credentials first', 'warning')
        return redirect(url_for('manage_credentials'))
    
    return render_template('launch_form.html', region=creds['region'])


@app.route('/api/launch-instance', methods=['POST'])
@login_required
def api_launch_instance():
    creds = current_user.get_aws_credentials(current_user.password_hash)
    
    if not creds:
        return jsonify({'success': False, 'message': 'AWS credentials not configured'})
    
    data = request.get_json()
    image_id = data.get('image_id')
    instance_type = data.get('instance_type')
    name = data.get('name')
    
    if not all([image_id, instance_type, name]):
        return jsonify({'success': False, 'message': 'Missing required parameters'})
    
    try:
        manager = AWSManager(creds['access_key'], creds['secret_key'], creds['region'])
        result = manager.launch_instance(image_id, instance_type, name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/api/terminate-instance', methods=['POST'])
@login_required
def api_terminate_instance():
    creds = current_user.get_aws_credentials(current_user.password_hash)
    
    if not creds:
        return jsonify({'success': False, 'message': 'AWS credentials not configured'})
    
    data = request.get_json()
    instance_id = data.get('instance_id')
    
    if not instance_id:
        return jsonify({'success': False, 'message': 'Instance ID is required'})
    
    try:
        manager = AWSManager(creds['access_key'], creds['secret_key'], creds['region'])
        result = manager.terminate_instance(instance_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/api/instances')
@login_required
def api_get_instances():
    creds = current_user.get_aws_credentials(current_user.password_hash)
    
    if not creds:
        return jsonify([])
    
    try:
        manager = AWSManager(creds['access_key'], creds['secret_key'], creds['region'])
        instances = manager.get_all_instances()
        return jsonify(instances)
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    with app.app_context():
        init_db(app)
    app.run(debug=True)
