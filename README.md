# VisualForm - AWS EC2 Instance Monitor

A Flask web application that provides a developer-friendly interface to view and monitor AWS EC2 instances. This is a **read-only monitoring tool** designed for developers to visualize their AWS resources without the ability to create or terminate instances.

## Features

✅ **User Authentication** - Secure login/register system with password hashing  
✅ **Encrypted Credentials** - AWS keys encrypted at rest using per-user Master Keys (PBKDF2 + Fernet)  
✅ **EC2 Dashboard** - Real-time list of all instances with detailed status information  
✅ **Instance Details** - View instance IDs, types, states, public/private IPs, and launch times  
✅ **Available Resources** - View key pairs, security groups, subnets, IAM roles, and instance types  
✅ **Multi-region Support** - Monitor instances across AWS regions  
✅ **Auto-refresh** - Dashboard updates every 30 seconds with latest instance data

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
│   └── dashboard.html     # Instance dashboard (read-only monitoring)
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

### Step 3: View Instances
- Navigate to "Dashboard" to see all EC2 instances
- View detailed information: instance ID, type, state, IPs, launch time
- Dashboard auto-refreshes every 30 seconds with latest data
- Browse available resources: key pairs, security groups, subnets, IAM roles, instance types

## Use Cases

VisualForm is perfect for:
- **Developers** - Quickly view your EC2 instances without AWS console navigation
- **DevOps Teams** - Monitor instances across multiple AWS regions from one dashboard
- **Learning** - Understand AWS resource relationships and current deployments
- **Audit** - View what resources currently exist in your AWS account

**Note:** This is a **read-only monitoring tool**. Resource creation and deletion are intentionally disabled to prevent accidental changes. Use AWS Console, Terraform, or CloudFormation for infrastructure changes.

## AWS Credentials

### Getting Your Credentials

1. Log into [AWS Console](https://console.aws.amazon.com)
2. Search for "IAM"
3. Click "Users" → select your user
4. Go to "Security credentials" tab
5. Click "Create access key"
6. Copy the Access Key ID and Secret Access Key
7. Use them in VisualForm

### Minimal IAM Policy (Read-Only)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeKeyPairs",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "iam:ListRoles"
      ],
      "Resource": "*"
    }
  ]
}
```

**This policy is read-only and prevents accidental resource modifications.**

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register` | GET/POST | Register new user |
| `/login` | GET/POST | Login |
| `/logout` | POST | Logout |
| `/credentials` | GET/POST | Manage AWS credentials |
| `/dashboard` | GET | View all instances (read-only) |
| `/api/instances` | GET | Get instances as JSON |
| `/api/key-pairs` | GET | Get available key pairs |
| `/api/security-groups` | GET | Get security groups |
| `/api/subnets` | GET | Get VPC subnets |
| `/api/iam-roles` | GET | Get IAM roles |
| `/api/instance-types` | GET | Get available instance types |

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
- Check IAM user has **read-only permissions** (see IAM Policy section)
- Ensure region is valid

### "No instances showing"
- Dashboard auto-refreshes every 30 seconds
- Verify AWS credentials are saved in the credentials page
- Check that you have instances running in the selected region
- Verify IAM permissions include `ec2:DescribeInstances`

### "Connection timeout" Error
- Check your network connectivity to AWS
- Verify AWS region is correct
- Check IAM role/user is not rate-limited

## Future Enhancements

- [ ] RDS instance browser (read-only)
- [ ] S3 bucket viewer (read-only)
- [ ] CloudFormation stack viewer (read-only)
- [ ] Cost analyzer and estimator
- [ ] Instance metrics dashboard (CPU, memory from CloudWatch)
- [ ] VPC and network topology visualization
- [ ] Export instance data to CSV/JSON

## License

MIT License - Use freely for educational and commercial purposes.

---

**Built with:** Flask, SQLAlchemy, Boto3, Cryptography  
**Database:** SQLite (dev), PostgreSQL (production)  
**Encryption:** PBKDF2 + Fernet  
