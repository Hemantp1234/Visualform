# VisualForm - AWS EC2 Instance Manager

A Flask web application that lets users manage AWS EC2 instances through an interactive GUI instead of Infrastructure-as-Code tools. This replaces Terraform for simple instance lifecycle management with a "Live State Engine."

## Features

✅ **User Authentication** - Secure login/register system with password hashing  
✅ **Encrypted Credentials** - AWS keys encrypted at rest using per-user Master Keys (PBKDF2 + Fernet)  
✅ **EC2 Dashboard** - Real-time list of all instances with status badges  
✅ **Launch Instances** - Create instances via form (no HCL needed)  
✅ **Terminate Instances** - Click-to-terminate with confirmation  
✅ **Instance Type Validation** - Checks availability before launching  
✅ **Multi-region Support** - Manage instances across AWS regions  

## Project Structure

```
visualform/
├── app.py                  # Main Flask application with routes
├── models.py               # SQLAlchemy User model with encryption
├── aws_services.py         # Boto3 wrapper for EC2 operations
├── requirements.txt        # Python dependencies
├── templates/
│   ├── base.html          # Base template with navbar
│   ├── login.html         # Login page
│   ├── register.html      # Registration page
│   ├── credentials.html   # AWS credentials form
│   ├── dashboard.html     # Instance dashboard (Live Map)
│   └── launch_form.html   # Create instance form
├── static/
│   └── css/
│       └── style.css      # Responsive styling
└── visualform.db          # SQLite database (auto-created)
```

## Security Architecture

### Master Key Derivation
Each user gets a **unique Master Key** derived from their credentials:

```
Master Key = PBKDF2(
    password = user_password,
    salt = base64(username) + username,
    iterations = 100,000,
    hash_algorithm = SHA256,
    dklen = 32
)
```

**Why this is secure:**
- Same password + username always generates same key (deterministic)
- Can regenerate without server-side storage
- Even if database stolen, AWS keys remain encrypted
- Key never transmitted over network
- Per-user isolation (different users = different keys)

### Encryption Flow
1. User enters AWS access key & secret key
2. Derive Master Key from user's password
3. Encrypt with `cryptography.Fernet`
4. Store ciphertext in database
5. On use: User authenticates → Master Key regenerated → Credentials decrypted

## Installation

### 1. Clone & Setup

```bash
cd /Users/hemantpatil/visualform
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or: venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
python3 app.py
```

The Flask app will auto-create `visualform.db` on first run.

### 4. Run the Application

```bash
python3 app.py
```

Navigate to `http://localhost:5000` in your browser.

## Usage Workflow

### Step 1: Register & Login
- Go to `/register` and create an account
- Username & password create your encryption Master Key

### Step 2: Configure AWS Credentials
- Navigate to "AWS Credentials" in navbar
- Enter AWS Access Key, Secret Key, and region
- Credentials are validated and encrypted

### Step 3: Launch Instances
- Click "Launch New Instance" from dashboard
- Fill form (AMI ID, instance type, name)
- Click "Launch Instance"
- Instance appears on dashboard in ~30 seconds

### Step 4: Terminate Instances
- On dashboard, find instance card
- Click "Terminate" button
- Confirm termination
- Instance state changes to "terminated"

## How It Replaces Terraform

| Feature | Terraform | VisualForm |
|---------|-----------|-----------|
| Configuration | HCL (text) | GUI (forms) |
| State Management | `.tfstate` file | Live AWS query |
| Plan/Apply | 2 steps | 1 click |
| Learning Curve | High (HCL syntax) | Low (web forms) |
| Instant Feedback | No (plan step) | Yes (auto-refresh) |
| Multi-user Support | Manual setup | Built-in |

**Example Comparison:**

Terraform:
```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  tags = { Name = "web-server" }
}
terraform plan
terraform apply
```

VisualForm:
```
1. Fill form on web page
2. Click "Launch Instance"
3. Done (auto-refresh shows new instance)
```

## AWS Credentials

### Getting Your Credentials

1. Log into [AWS Console](https://console.aws.amazon.com)
2. Search for "IAM"
3. Click "Users" → select your user
4. Go to "Security credentials" tab
5. Click "Create access key"
6. Copy the Access Key ID and Secret Access Key
7. Use them in VisualForm

### Minimal IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceTypes",
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    }
  ]
}
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register` | GET/POST | Register new user |
| `/login` | GET/POST | Login |
| `/logout` | POST | Logout |
| `/credentials` | GET/POST | Manage AWS credentials |
| `/dashboard` | GET | View all instances |
| `/launch-form` | GET | Launch instance form |
| `/api/launch-instance` | POST | Create instance (JSON) |
| `/api/terminate-instance` | POST | Terminate instance (JSON) |
| `/api/instances` | GET | Get instances as JSON |

## Development Notes

### Adding More AWS Services
Edit `aws_services.py` to add RDS, S3, Lambda management, etc.

### Database Migrations
To reset database:
```bash
rm visualform.db
python3 app.py
```

### Debugging
Set `debug=False` in production. Enable logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Deployment

### Pre-Production Checklist
- [ ] Change `SECRET_KEY` to random string
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/SSL
- [ ] Implement rate limiting
- [ ] Add audit logging for credential access
- [ ] Use AWS KMS for Master Key storage (optional)
- [ ] Deploy behind reverse proxy (nginx)
- [ ] Set up CSRF protection

### Deploy to AWS Lambda/EC2
See AWS documentation for Flask deployment best practices.

## Troubleshooting

### "Invalid AWS credentials" Error
- Verify Access Key ID and Secret Key are correct
- Check IAM user has required permissions
- Ensure region is valid

### "Instance type not available"
- Instance type not available in selected region
- Try t2.micro (most widely available)

### "No instances showing"
- Dashboard auto-refreshes every 30 seconds
- Try manual refresh if instances take longer to appear

## Future Enhancements

- [ ] RDS database management interface
- [ ] S3 bucket browser
- [ ] CloudFormation template builder
- [ ] Cost estimator
- [ ] Scheduled snapshots
- [ ] Instance metrics dashboard (CPU, memory)
- [ ] Bulk instance operations
- [ ] Backup/restore interface

## License

MIT License - Use freely for educational and commercial purposes.

---

**Built with:** Flask, SQLAlchemy, Boto3, Cryptography  
**Database:** SQLite (dev), PostgreSQL (production)  
**Encryption:** PBKDF2 + Fernet  
