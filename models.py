from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import os
import base64
from hashlib import pbkdf2_hmac

db = SQLAlchemy()


def derive_master_key(username, password, salt=None):
    """
    Derive a unique Master Key for each user from their username and password.
    Uses PBKDF2 to generate a cryptographic key.
    
    Args:
        username: User's username
        password: User's password (plaintext)
        salt: Optional pre-computed salt (for consistency)
    
    Returns:
        tuple: (master_key_bytes, salt_bytes)
    """
    if salt is None:
        # Generate a consistent salt from username
        salt = base64.b64encode(username.encode()).ljust(16, b'=')[:16]
    
    # PBKDF2 to derive key from password and username
    master_key_bytes = pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt + username.encode(),
        100000,
        dklen=32
    )
    
    return master_key_bytes, salt


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # AWS Credentials (encrypted)
    aws_access_key_encrypted = db.Column(db.Text, nullable=True)
    aws_secret_key_encrypted = db.Column(db.Text, nullable=True)
    aws_region = db.Column(db.String(50), default='us-east-1', nullable=False)
    
    # Salt for key derivation (stored plainly - it's not a secret)
    key_derivation_salt = db.Column(db.LargeBinary, nullable=False)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def get_master_key(self, password):
        """
        Regenerate the user's Master Key using their password.
        
        Args:
            password: User's plaintext password
        
        Returns:
            bytes: The decryption key (base64-encoded for Fernet)
        """
        master_key_bytes, _ = derive_master_key(self.username, password, self.key_derivation_salt)
        # Fernet requires a base64-encoded 32-byte key
        return base64.urlsafe_b64encode(master_key_bytes)
    
    def set_aws_credentials(self, access_key, secret_key, region, password):
        """
        Encrypt and store AWS credentials using the user's Master Key.
        
        Args:
            access_key: AWS Access Key ID
            secret_key: AWS Secret Access Key
            region: AWS Region
            password: User's plaintext password (to derive Master Key)
        """
        master_key = self.get_master_key(password)
        cipher = Fernet(master_key)
        
        self.aws_access_key_encrypted = cipher.encrypt(access_key.encode()).decode()
        self.aws_secret_key_encrypted = cipher.encrypt(secret_key.encode()).decode()
        self.aws_region = region
    
    def get_aws_credentials(self, password):
        """
        Decrypt and retrieve AWS credentials.
        
        Args:
            password: User's plaintext password (to derive Master Key)
        
        Returns:
            dict: {'access_key': str, 'secret_key': str, 'region': str} or None if not set
        """
        if not self.aws_access_key_encrypted or not self.aws_secret_key_encrypted:
            return None
        
        try:
            master_key = self.get_master_key(password)
            cipher = Fernet(master_key)
            
            access_key = cipher.decrypt(self.aws_access_key_encrypted.encode()).decode()
            secret_key = cipher.decrypt(self.aws_secret_key_encrypted.encode()).decode()
            
            return {
                'access_key': access_key,
                'secret_key': secret_key,
                'region': self.aws_region
            }
        except Exception as e:
            print(f"Error decrypting credentials: {e}")
            return None


def init_db(app):
    """Initialize the database."""
    with app.app_context():
        db.create_all()
