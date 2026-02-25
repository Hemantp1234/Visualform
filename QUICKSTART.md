# Quick Start Guide

## 5-Minute Setup

```bash
# 1. Navigate to project
cd /Users/hemantpatil/visualform

# 2. Run setup
chmod +x setup.sh
./setup.sh

# 3. Activate environment
source venv/bin/activate

# 4. Start Flask
python3 app.py

# 5. Open http://localhost:5000
```

---

## First Launch Checklist

- [ ] Get AWS credentials (Access Key + Secret Key from IAM)
- [ ] Register account at http://localhost:5000/register
- [ ] Go to AWS Credentials → Enter keys → Save
- [ ] Go to Dashboard → Launch New Instance
- [ ] Select AMI (e.g., ami-0c55b159cbfafe1f0 for Ubuntu 22.04)
- [ ] Select instance type (t2.micro is free tier)
- [ ] Enter instance name
- [ ] Click Launch
- [ ] Instance appears in ~30 seconds

---

## Common AMI IDs (us-east-1)

| OS | AMI ID | Notes |
|----|--------|-------|
| Ubuntu 22.04 LTS | ami-0c55b159cbfafe1f0 | Recommended for beginners |
| Amazon Linux 2 | ami-0533def491c57d991 | AWS-optimized |
| Windows Server 2022 | ami-0c9bcc78d551d0bb8 | Windows-based |

---

## Security: Master Key Explanation

Your AWS credentials are **never stored in plain text**. Instead:

1. When you register, we create a Master Key from your password
2. This Master Key encrypts your AWS credentials
3. The encrypted credentials are stored in the database
4. Only your password can decrypt them

**If database is stolen:** AWS keys still protected ✅

---

## Troubleshooting

### App won't start
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version (need 3.8+)
python3 --version
```

### Can't connect to AWS
```
1. Verify Access Key ID is correct
2. Verify Secret Key is correct (starts with wJalr... pattern)
3. Ensure region is valid (us-east-1, eu-west-1, etc.)
4. Check IAM user has EC2 permissions
```

### Instances not showing
```
1. Refresh page (Ctrl+R or Cmd+R)
2. Dashboard auto-refreshes every 30 seconds
3. Check you're in correct AWS region
4. Verify AWS credentials are saved
```

---

## File Quick Reference

| File | Purpose | Edit? |
|------|---------|-------|
| app.py | Flask routes | Advanced only |
| models.py | Database encryption | Do not modify |
| aws_services.py | AWS integration | Add features here |
| requirements.txt | Dependencies | Add packages here |
| templates/ | HTML pages | Customize styling |
| static/css/ | Styling | Customize colors |

---

## Useful Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Install new package
pip install <package-name>

# Run Flask in debug mode (default)
python3 app.py

# Run Flask in production
export FLASK_ENV=production
python3 app.py

# Reset database (WARNING: deletes all users!)
rm visualform.db
python3 app.py

# Deactivate virtual environment
deactivate

# View Flask routes
python3 -c "from app import app; print([rule.rule for rule in app.url_map.iter_rules()])"
```

---

## Adding New Features

### Add RDS Management
Edit `aws_services.py`:
```python
def create_rds_instance(self, db_id, instance_type):
    rds_client = boto3.client('rds', ...)
    # Add RDS logic here
```

### Add Email Notifications
Edit `requirements.txt`:
```
Flask-Mail==0.9.1
```
Then in `app.py`:
```python
from flask_mail import Mail
mail = Mail(app)
```

### Add Database Migrations
```bash
pip install Flask-Migrate
flask db init
flask db migrate
flask db upgrade
```

---

## Deployment Options

### AWS Elastic Beanstalk
```bash
pip install awsebcli
eb init
eb create
eb deploy
```

### Heroku
```bash
pip install gunicorn
echo "web: gunicorn app:app" > Procfile
git push heroku main
```

### Docker
```dockerfile
FROM python:3.9
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "app:app"]
```

---

## Database Structure

```
Users Table
├── id (primary key)
├── username (unique)
├── password_hash
├── aws_access_key_encrypted
├── aws_secret_key_encrypted
├── aws_region
└── key_derivation_salt
```

---

## Security Best Practices

✅ **Do This:**
- Use strong passwords (12+ characters)
- Keep AWS credentials private
- Change SECRET_KEY in production
- Use HTTPS in production
- Enable MFA on AWS account
- Regularly rotate access keys

❌ **Don't Do This:**
- Store AWS keys in git
- Share database backups
- Use weak passwords
- Use debug mode in production
- Hardcode SECRET_KEY
- Share credentials via email

---

## Performance Tips

1. **Dashboard slow?** - Reduce auto-refresh from 30s to 60s in dashboard.html
2. **Many instances?** - Add pagination in templates/dashboard.html
3. **Slow encryption?** - PBKDF2 uses 100k iterations (security vs speed tradeoff)
4. **Database large?** - Switch to PostgreSQL for production

---

## Support

For issues:
1. Check IMPLEMENTATION.md for detailed docs
2. Check README.md for full guide
3. Review error messages in Flask console
4. Check AWS CloudTrail for API errors

---

**Last Updated:** February 25, 2026  
**Version:** 1.0.0 - Production Ready
