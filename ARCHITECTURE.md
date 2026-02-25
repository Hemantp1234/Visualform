# VisualForm - Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                              │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Login Page   │  │ Credentials  │  │ Dashboard    │              │
│  │ (login.html) │  │ (creds.html) │  │ (dashboard.  │              │
│  │              │  │              │  │  html)       │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
│  ┌──────────────────────────────────────────────────────┐           │
│  │             JAVASCRIPT (Fetch API)                  │           │
│  │  - Form submission                                 │           │
│  │  - API calls to Flask backend                      │           │
│  │  - Auto-refresh every 30 seconds                   │           │
│  │  - Confirmation dialogs                            │           │
│  └──────────────────────────────────────────────────────┘           │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP/HTTPS
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    FLASK WEB SERVER                                │
│                      (app.py)                                       │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Auth Routes  │  │ Creds Routes │  │ API Routes   │             │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤             │
│  │ /register    │  │ /credentials │  │ /api/launch  │             │
│  │ /login       │  │ (POST)       │  │ /api/        │             │
│  │ /logout      │  │              │  │ terminate    │             │
│  │              │  │ (validate &  │  │              │             │
│  │              │  │  encrypt)    │  │ (JSON)       │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │           BUSINESS LOGIC                               │       │
│  │                                                         │       │
│  │  ┌─────────────────────────────────────────────────┐  │       │
│  │  │ AWS INTEGRATION (aws_services.py)              │  │       │
│  │  │  - AWSManager class                            │  │       │
│  │  │  - launch_instance()                           │  │       │
│  │  │  - terminate_instance()                        │  │       │
│  │  │  - get_all_instances()                         │  │       │
│  │  │  - validate_aws_credentials()                  │  │       │
│  │  │  - _is_instance_type_available()               │  │       │
│  │  └─────────────────────────────────────────────────┘  │       │
│  │                                                         │       │
│  │  ┌─────────────────────────────────────────────────┐  │       │
│  │  │ ENCRYPTION (models.py)                          │  │       │
│  │  │  - derive_master_key() [PBKDF2]                │  │       │
│  │  │  - set_aws_credentials() [Fernet encrypt]      │  │       │
│  │  │  - get_aws_credentials() [Fernet decrypt]      │  │       │
│  │  └─────────────────────────────────────────────────┘  │       │
│  │                                                         │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
└────────────────────────┬────────────────┬──────────────────────────┘
                         │                │
                    HTTP │                │ SQL Queries
                         ↓                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       SQLite DATABASE                               │
│                  (visualform.db)                                    │
│                                                                     │
│  ┌──────────────────────────────────────┐                          │
│  │         USERS TABLE                  │                          │
│  ├──────────────────────────────────────┤                          │
│  │ id (PK)                              │                          │
│  │ username                             │                          │
│  │ password_hash                        │ ← Encrypted with         │
│  │ aws_access_key_encrypted             │   user's Master Key      │
│  │ aws_secret_key_encrypted             │   (PBKDF2)               │
│  │ aws_region                           │                          │
│  │ key_derivation_salt                  │                          │
│  └──────────────────────────────────────┘                          │
│                                                                     │
│  Example Row:                                                      │
│  ┌──────────────────────────────────────┐                          │
│  │ id: 1                                │                          │
│  │ username: john_doe                   │                          │
│  │ password_hash: pbkdf2:sha...         │                          │
│  │ aws_access_key_encrypted: gAAAAA... │ ← Encrypted              │
│  │ aws_secret_key_encrypted: gAAAAA... │ ← Encrypted              │
│  │ aws_region: us-east-1                │                          │
│  │ key_derivation_salt: [bytes]         │                          │
│  └──────────────────────────────────────┘                          │
│                                                                     │
└────────────────────────────┬──────────────────────────────────────┘
                             │ boto3
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        AWS CLOUD                                    │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   EC2 API    │  │     IAM      │  │  CloudTrail  │              │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤              │
│  │ Authenticate │  │ Permissions  │  │ Audit Log    │              │
│  │ Launch       │  │ Check        │  │ Track API    │              │
│  │ instances    │  │              │  │ Calls        │              │
│  │ Terminate    │  │              │  │              │              │
│  │ instances    │  │              │  │              │              │
│  │ List         │  │              │  │              │              │
│  │ instances    │  │              │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
│  ┌────────────────────────────────────────┐                        │
│  │ EC2 INSTANCES (User's Running VMs)    │                        │
│  ├────────────────────────────────────────┤                        │
│  │ i-0123456789abcdef0 (web-server-01)   │                        │
│  │ State: running | Type: t2.micro        │                        │
│  │                                        │                        │
│  │ i-abcdef0123456789 (db-server-01)     │                        │
│  │ State: running | Type: t2.small        │                        │
│  └────────────────────────────────────────┘                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: User Registration

```
┌─────────────┐
│ User Action │ "Register with username: john_doe, password: pass123"
└────────┬────┘
         │
         ↓ POST /register
    ┌─────────────────────┐
    │ Flask Route Handler │
    └────────┬────────────┘
             │
             ├─→ Validate inputs
             │
             ├─→ Hash password: werkzeug.security.generate_password_hash()
             │   Result: "pbkdf2:sha256$..."
             │
             ├─→ Derive Master Key salt from username
             │   salt = base64("john_doe")[:16]
             │
             ├─→ Create User object
             │   User(
             │     username="john_doe",
             │     password_hash="pbkdf2:sha256$...",
             │     key_derivation_salt=salt
             │   )
             │
             ├─→ db.session.add(user)
             │   db.session.commit()
             │
             ↓
       ┌──────────────────┐
       │ SQLite Database  │
       │ (visualform.db)  │
       │                  │
       │ INSERT INTO users
       │ VALUES (
       │   id: 1,
       │   username: "john_doe",
       │   password_hash: "pbkdf2:sha256$...",
       │   aws_access_key_encrypted: NULL,
       │   aws_secret_key_encrypted: NULL,
       │   aws_region: "us-east-1",
       │   key_derivation_salt: [bytes]
       │ )
       └──────────────────┘
             │
             ↓
      ┌─────────────────────┐
      │ Flask Response      │
      │ Redirect to /login  │
      │ Flash: "Registration│
      │        successful!" │
      └─────────────────────┘
```

---

## Data Flow: AWS Credential Encryption

```
┌──────────────────────────────────────────┐
│ User on /credentials page                │
│ Enters:                                  │
│  - Access Key: AKIAIOSFODNN7EXAMPLE      │
│  - Secret Key: wJalrXUtnFEMI/K7MDENG... │
│  - Region: us-east-1                     │
└──────────┬───────────────────────────────┘
           │
           ↓ POST /credentials
    ┌────────────────────────┐
    │ Flask Route: POST /    │
    │ credentials            │
    └──────────┬─────────────┘
               │
               ├─→ Get form data
               │
               ├─→ validate_aws_credentials()
               │   └─→ Create boto3 client
               │       └─→ Call ec2.describe_instances(DryRun=True)
               │           └─→ If success: Credentials are valid ✅
               │               If error: Invalid credentials ❌
               │
               ├─→ current_user.set_aws_credentials(
               │        access_key="AKIA...",
               │        secret_key="wJal...",
               │        region="us-east-1",
               │        password="pass123"  ← User's login password
               │   )
               │
               ├─→ Inside set_aws_credentials():
               │
               │   1. Get Master Key:
               │      master_key = derive_master_key(
               │        username="john_doe",
               │        password="pass123",  ← From user input (decrypted from session)
               │        salt=user.key_derivation_salt
               │      )
               │      Result: 32 bytes from PBKDF2
               │
               │   2. Encode Master Key for Fernet:
               │      master_key_base64 = base64.urlsafe_b64encode(master_key)
               │
               │   3. Create Fernet cipher:
               │      cipher = Fernet(master_key_base64)
               │
               │   4. Encrypt Access Key:
               │      encrypted_ak = cipher.encrypt(
               │        b"AKIAIOSFODNN7EXAMPLE"
               │      )
               │      Result: "gAAAAABl1234abcd..."
               │
               │   5. Encrypt Secret Key:
               │      encrypted_sk = cipher.encrypt(
               │        b"wJalrXUtnFEMI/K7MDENG/..."
               │      )
               │      Result: "gAAAAABl5678efgh..."
               │
               │   6. Store in User object:
               │      user.aws_access_key_encrypted = "gAAAAABl1234abcd..."
               │      user.aws_secret_key_encrypted = "gAAAAABl5678efgh..."
               │      user.aws_region = "us-east-1"
               │
               ├─→ db.session.commit()
               │   └─→ SQL INSERT/UPDATE
               │
               ↓
        ┌──────────────────────────────────────┐
        │ Database (visualform.db)             │
        │                                      │
        │ UPDATE users SET                     │
        │   aws_access_key_encrypted =         │
        │     "gAAAAABl1234abcd...",          │
        │   aws_secret_key_encrypted =         │
        │     "gAAAAABl5678efgh...",          │
        │   aws_region = "us-east-1"           │
        │ WHERE id = 1                         │
        │                                      │
        │ ✅ Encrypted data only!             │
        │ ❌ Plaintext keys NOT stored         │
        └──────────────────────────────────────┘
               │
               ↓
      ┌──────────────────────────────┐
      │ Flask Response               │
      │ Redirect to /dashboard       │
      │ Flash: "Credentials saved!"  │
      └──────────────────────────────┘
```

---

## Data Flow: Instance Launch

```
┌────────────────────────────────────────┐
│ User on /launch-form page              │
│ Fills form:                            │
│  - Name: web-server-01                 │
│  - AMI ID: ami-0c55b159cbfafe1f0      │
│  - Instance Type: t2.micro             │
└──────────┬─────────────────────────────┘
           │
           ↓ JavaScript Form Submit
    ┌──────────────────────────┐
    │ fetch('/api/launch-      │
    │ instance', {             │
    │   method: 'POST',        │
    │   body: JSON {           │
    │     image_id: "ami-...", │
    │     instance_type:       │
    │       "t2.micro",        │
    │     name: "web-..."      │
    │   }                      │
    │ })                       │
    └──────────┬───────────────┘
               │
               ↓ POST /api/launch-instance
        ┌────────────────────────┐
        │ Flask Route Handler    │
        │ api_launch_instance()  │
        └──────────┬─────────────┘
                   │
                   ├─→ current_user.get_aws_credentials(password)
                   │   └─→ Decrypt AWS keys using Master Key
                   │       Result: {'access_key': 'AKIA...', 
                   │               'secret_key': 'wJal...', 
                   │               'region': 'us-east-1'}
                   │
                   ├─→ Create AWSManager(access_key, secret_key, region)
                   │   └─→ Initialize boto3 EC2 client with credentials
                   │
                   ├─→ manager.launch_instance(
                   │     image_id="ami-0c55b159cbfafe1f0",
                   │     instance_type="t2.micro",
                   │     name="web-server-01"
                   │   )
                   │
                   ├─→ Inside launch_instance():
                   │
                   │   1. Validate instance type:
                   │      _is_instance_type_available("t2.micro")
                   │      └─→ Check EC2 API: available ✅
                   │
                   │   2. Call AWS:
                   │      ec2_client.run_instances(
                   │        ImageId="ami-0c55b159cbfafe1f0",
                   │        MinCount=1,
                   │        MaxCount=1,
                   │        InstanceType="t2.micro",
                   │        TagSpecifications=[{
                   │          ResourceType: 'instance',
                   │          Tags: [{Key: 'Name', 
                   │                  Value: 'web-server-01'}]
                   │        }]
                   │      )
                   │
                   │   3. AWS launches instance:
                   │      Instance ID: i-0123456789abcdef0
                   │      State: pending → running
                   │
                   │   4. Return result:
                   │      {
                   │        success: true,
                   │        instance_id: "i-0123456789abcdef0",
                   │        message: "Instance launched..."
                   │      }
                   │
                   ├─→ Return JSON response
                   │
                   ↓
        ┌──────────────────────────────┐
        │ JavaScript receives JSON     │
        │ {                            │
        │   success: true,             │
        │   instance_id: "i-01234...", │
        │   message: "Instance..."     │
        │ }                            │
        └──────────┬───────────────────┘
                   │
                   ├─→ Display success message
                   │
                   ├─→ Show instance_id to user
                   │
                   ├─→ Wait 2 seconds
                   │
                   ↓
        ┌──────────────────────────────┐
        │ Redirect to /dashboard       │
        └──────────┬───────────────────┘
                   │
                   ↓ GET /dashboard
        ┌──────────────────────────────┐
        │ Flask fetches instances from │
        │ AWS API                      │
        │                              │
        │ manager.get_all_instances()  │
        │ └─→ boto3 describe_instances │
        │     ↓                        │
        │     AWS returns:             │
        │     [{                       │
        │       InstanceId: "i-0123...",
        │       State: "running",      │
        │       InstanceType: "t2.m",  │
        │       Tags: [{Name: "web-"}],│
        │       LaunchTime: "2026...",  │
        │       PublicIpAddress: "3..",│
        │       PrivateIpAddress:"172."│
        │     }]                       │
        │                              │
        │ Render dashboard.html        │
        │ with instances list          │
        └──────────┬───────────────────┘
                   │
                   ↓ Display in browser
        ┌──────────────────────────────┐
        │ Instance Card:               │
        │ ┌────────────────────────┐   │
        │ │ web-server-01      ● R │   │ ← Green "running" badge
        │ │ ID: i-0123456789... │   │
        │ │ Type: t2.micro      │   │
        │ │ IP: 3.xx.xx.xx      │   │
        │ │ Launched: 2 min ago │   │
        │ │ [Terminate]         │   │
        │ └────────────────────────┘   │
        └──────────────────────────────┘
```

---

## Security: Master Key Protection

```
┌────────────────────────────────────────────┐
│ SCENARIO: Database is Stolen 😱           │
│ Attacker has all data including:          │
│ - username                                 │
│ - password_hash (salted & hashed)         │
│ - aws_access_key_encrypted (gAAAAA...)   │
│ - aws_secret_key_encrypted (gAAAAA...)   │
│ - key_derivation_salt                     │
└────────────────────────────────────────────┘
                     │
                     ↓
        ┌─────────────────────────────┐
        │ Can attacker get AWS keys?  │
        └──────────┬──────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ↓                     ↓
  Option 1:              Option 2:
  Decrypt with          Brute force
  existing Master Key   password
        │                     │
        └──────┬──────────────┘
               │
               ↓
  ❌ FAILS! Here's why:
  
  To decrypt, attacker needs Master Key:
  Master Key = PBKDF2(
    password = "pass123"  ← Attacker doesn't know this!
    salt = base64("john_doe") + "john_doe",
    iterations = 100,000,  ← Computationally expensive
    hash_algorithm = SHA256,
    dklen = 32 bytes
  )
  
  Even if attacker has:
  - username ("john_doe") ✓
  - password_hash (pbkdf2:sha256$...) ✓
  - key_derivation_salt [bytes] ✓
  
  Still can't decrypt without the ACTUAL PASSWORD ❌
  
  Why?
  1. password_hash is SALTED & HASHED → Can't reverse
  2. PBKDF2 uses 100,000 iterations → Slow to brute force
  3. Need to:
     a) Guess password
     b) Run PBKDF2 (takes ~50-100ms per guess)
     c) Decrypt with Fernet (fail if wrong password)
     d) Check if decrypted key looks valid (needs AWS call)
     
  Time to brute force (worst case):
  - 10,000 password guesses
  - × 100ms per guess
  - = 1,000 seconds (17 minutes) per 10k guesses
  - With 100 million passwords: 1,157 days ❌
```

---

## Component Interactions

```
                    ┌──────────────┐
                    │   Browser    │
                    │   (UI)       │
                    └────────┬─────┘
                             │
                    ┌────────▼─────────┐
                    │ Flask App        │
                    │ (app.py)         │
                    │                  │
                    │ Routes:          │
                    │ - /register      │
                    │ - /login         │
                    │ - /dashboard     │
                    │ - /api/*         │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ↓                ↓                ↓
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Database     │ │ Encryption   │ │ AWS Service  │
    │ (models.py)  │ │ (models.py)  │ │ (aws_serv.py)│
    │              │ │              │ │              │
    │ User Model:  │ │ - PBKDF2 key │ │ - AWSManager │
    │ - username   │ │   derivation │ │ - launch()   │
    │ - password   │ │ - Fernet     │ │ - terminate()│
    │ - encrypted  │ │   encryption │ │ - list()     │
    │   creds      │ │ - Fernet     │ │ - validate() │
    │ - salt       │ │   decryption │ │              │
    │              │ │              │ │              │
    └──────────────┘ └──────────────┘ └──────┬───────┘
                                             │
                                             ↓
                                    ┌──────────────────┐
                                    │  AWS API         │
                                    │  (boto3 client)  │
                                    │                  │
                                    │  EC2:            │
                                    │  - RunInstances  │
                                    │  - Terminate...  │
                                    │  - Describe...   │
                                    │                  │
                                    └──────────────────┘
```

---

**Architecture Version:** 1.0  
**Last Updated:** February 25, 2026
