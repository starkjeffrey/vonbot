# Getting Started with Legacy Adapter Service

**Complete step-by-step guide from zero to production**

## 📋 Prerequisites

Before you begin, ensure you have:

- [ ] Docker installed on Mac M2
- [ ] Docker installed on Ubuntu VPS
- [ ] SSH access to your VPS
- [ ] Administrator access to Windows 11 (MSSQL server)
- [ ] Legacy MSSQL connection details (host, port, username, password, database name)

## 🎯 Overview

This guide will walk you through:

1. **Local Testing** (Mac M2) - Test the adapter service locally
2. **VPS Deployment** - Deploy to your secure Ubuntu VPS
3. **Windows Lockdown** - Secure the MSSQL server
4. **Django Integration** - Connect Django to the adapter
5. **Verification** - Ensure everything works end-to-end

**Estimated Time:** 30-45 minutes

---

## Step 1: Local Testing on Mac M2 (15 minutes)

### 1.1 Navigate to Adapter Directory

```bash
cd /Users/jeffreystark/Development/key/naga-monorepo-v2/backend/services/legacy-adapter
```

### 1.2 Create Environment File

```bash
cp .env.example .env
```

### 1.3 Edit Configuration

```bash
nano .env
```

Update these values:

```bash
# Your legacy MSSQL connection
LEGACY_DB_HOST=your-legacy-server.example.com
LEGACY_DB_PORT=14433                    # Your special port
LEGACY_DB_USER=sa
LEGACY_DB_PASSWORD=123456               # Yes, we know it's terrible
LEGACY_DB_NAME=LegacySIS

# Generate API key: openssl rand -hex 32
API_KEY=paste-generated-key-here

# Local development settings
DEBUG=true
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

Save and exit (Ctrl+X, Y, Enter).

### 1.4 Generate Secure API Key

```bash
openssl rand -hex 32
```

Copy the output and paste it as `API_KEY` in your `.env` file.

### 1.5 Run Local Test

```bash
./scripts/test-local.sh
```

Expected output:

```
🧪 Testing Legacy Adapter Service Locally...
✅ Found .env file
🔨 Building Docker image...
🚀 Starting service...
⏳ Waiting for service to be healthy...
✅ Service is healthy!

🧪 Running health check tests...
Test 1: Health Check
✅ Health check passed

Test 2: Database Connectivity
✅ Database connection successful

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All tests passed!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 1.6 Test API Endpoints

```bash
./scripts/test-api.sh your-api-key-from-env-file
```

Expected output:

```
🧪 Testing Legacy Adapter API
Test 1: Health Check (No Auth)
✅ PASSED

Test 2: Unauthorized Access (Should Fail)
✅ PASSED - Correctly rejected unauthorized request

Test 3: Create Student
✅ PASSED - Student created with legacy ID: 98765

...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All API tests passed!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

✅ **Checkpoint 1**: If all tests pass, the adapter works on your Mac!

---

## Step 2: VPS Deployment (10 minutes)

### 2.1 Copy Files to VPS

From your Mac:

```bash
# Option A: If VPS has git access
ssh user@vps.example.com
git clone https://github.com/yourorg/naga-monorepo-v2.git
cd naga-monorepo-v2/backend/services/legacy-adapter

# Option B: Direct copy
cd /Users/jeffreystark/Development/key/naga-monorepo-v2/backend/services
scp -r legacy-adapter user@vps.example.com:~/
```

### 2.2 Configure VPS Environment

SSH into VPS:

```bash
ssh user@vps.example.com
cd ~/legacy-adapter
```

Create `.env` file:

```bash
cp .env.example .env
nano .env
```

Update for production:

```bash
# Legacy MSSQL connection
LEGACY_DB_HOST=your-legacy-server.example.com
LEGACY_DB_PORT=14433
LEGACY_DB_USER=sa
LEGACY_DB_PASSWORD=123456
LEGACY_DB_NAME=LegacySIS

# Same API key as local (or generate new one)
API_KEY=same-key-from-step-1

# Production settings
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=legacy-adapter.vps.example.com
```

### 2.3 Deploy Service

```bash
./scripts/deploy-vps.sh
```

Expected output:

```
🚀 Deploying Legacy Adapter Service to VPS...
✅ Configuration validated
🔨 Building Docker image...
🚀 Starting service...
✅ Service is healthy!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Deployment complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Service is running at:
  - http://localhost:8001 (local)
  - http://203.0.113.50:8001 (network)
```

### 2.4 Set Up SSL with Caddy

On VPS:

```bash
# Install Caddy
sudo apt install -y caddy

# Create Caddyfile
sudo tee /etc/caddy/Caddyfile << EOF
legacy-adapter.vps.example.com {
    reverse_proxy localhost:8001
}
EOF

# Reload Caddy (auto-provisions SSL!)
sudo systemctl reload caddy
```

### 2.5 Test from Mac

From your Mac:

```bash
curl https://legacy-adapter.vps.example.com/health
```

Expected response:

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-30T10:15:23Z",
  "version": "1.0.0"
}
```

✅ **Checkpoint 2**: If you get this response, the VPS deployment works!

---

## Step 3: Windows MSSQL Lockdown (5 minutes)

### 3.1 Get VPS Public IP

From VPS:

```bash
curl ifconfig.me
```

Copy the IP address (e.g., `203.0.113.50`).

### 3.2 Run Firewall Script

On Windows 11 machine:

1. Open PowerShell **as Administrator**
2. Navigate to the scripts directory
3. Run dry-run first:

```powershell
cd C:\path\to\legacy-adapter\scripts
.\lockdown-mssql.ps1 -VpsIP "203.0.113.50" -MssqlPort 14433 -DryRun
```

4. If dry-run looks good, run for real:

```powershell
.\lockdown-mssql.ps1 -VpsIP "203.0.113.50" -MssqlPort 14433
```

Expected output:

```
═══════════════════════════════════════════════════════════
🔒 MSSQL Server Firewall Lockdown Script
═══════════════════════════════════════════════════════════

Step 1: Removing old firewall rules...
  Removing old 'MSSQL Legacy Access' rules... ✅

Step 2: Creating new firewall rules...
  Allow connections from VPS (203.0.113.50)... ✅
  Block all other connections to port 14433... ✅

═══════════════════════════════════════════════════════════
✅ Firewall lockdown complete!
═══════════════════════════════════════════════════════════

Security Status:
  ✅ MSSQL port 14433 is now protected
  ✅ Only VPS IP 203.0.113.50 can connect
  ✅ All other connection attempts will be blocked
```

### 3.3 Verify Lockdown

From a random computer (NOT your VPS):

```bash
telnet legacy-server.example.com 14433
# Should FAIL with "Connection refused" or timeout ✅
```

From VPS:

```bash
telnet legacy-server.example.com 14433
# Should SUCCEED and connect ✅
```

✅ **Checkpoint 3**: MSSQL is now locked down to VPS only!

---

## Step 4: Django Integration (5 minutes)

### 4.1 Stop Local Adapter Service

If still running from Step 1:

```bash
cd /Users/jeffreystark/Development/key/naga-monorepo-v2/backend/services/legacy-adapter
docker compose -f docker-compose.dev.yml down
```

### 4.2 Update Django Environment

On your Mac, edit `backend/.env`:

```bash
cd /Users/jeffreystark/Development/key/naga-monorepo-v2/backend
nano .env
```

Add these lines:

```bash
# Legacy Adapter Configuration
LEGACY_SYNC_ENABLED=true
LEGACY_ADAPTER_URL=https://legacy-adapter.vps.example.com
LEGACY_ADAPTER_API_KEY=same-api-key-as-adapter-service
LEGACY_ADAPTER_TIMEOUT=10
```

### 4.3 Test Django Integration

Open Django shell:

```bash
# From backend/ directory
docker compose -f docker-compose.local.yml run --rm django python manage.py shell
```

Test the service:

```python
from apps.level_testing.services.legacy_sync import legacy_sync_service
from apps.people.models import StudentProfile

# Get a student
student = StudentProfile.objects.first()

# Try syncing to legacy
try:
    legacy_id = legacy_sync_service.create_student(student)
    print(f"✅ Synced to legacy! Legacy ID: {legacy_id}")
except Exception as e:
    print(f"❌ Error: {e}")
```

✅ **Checkpoint 4**: If you see "Synced to legacy!", Django integration works!

---

## Step 5: Verification (5 minutes)

### 5.1 End-to-End Test

Create a complete workflow test:

```python
# In Django shell
from apps.people.models import Person, StudentProfile
from apps.level_testing.services.legacy_sync import legacy_sync_service
from django.utils import timezone

# Create a test person
person = Person.objects.create(
    first_name="Test",
    last_name="Student",
    date_of_birth=timezone.now().date(),
    gender="M"
)

# Create student profile
student = StudentProfile.objects.create(
    person=person,
    student_id=99999,  # Test ID
    status="ACTIVE"
)

# Sync to legacy
legacy_id = legacy_sync_service.create_student(student)
print(f"✅ Created in Django: {student.student_id}")
print(f"✅ Synced to legacy: {legacy_id}")

# Verify in legacy
legacy_record = legacy_sync_service.get_student(student.student_id)
print(f"✅ Retrieved from legacy: {legacy_record}")
```

### 5.2 Monitor Service

On VPS, start monitoring:

```bash
cd ~/legacy-adapter
./scripts/monitor.sh 30
```

You should see:

```
🔍 Monitoring Legacy Adapter Service
Service URL: http://localhost:8001
Check interval: 30s
Press Ctrl+C to stop

[2024-01-30 10:15:23] ✅ Healthy - Database: connected
[2024-01-30 10:15:53] ✅ Healthy - Database: connected
[2024-01-30 10:16:23] ✅ Healthy - Database: connected
```

✅ **Checkpoint 5**: If monitoring shows healthy, you're all set!

---

## 🎉 Success!

You've successfully:

- ✅ Tested adapter locally on Mac M2
- ✅ Deployed adapter to VPS with SSL
- ✅ Locked down MSSQL to VPS only
- ✅ Integrated Django with adapter
- ✅ Verified end-to-end functionality

## 📚 Next Steps

1. **Enable for Production**
   - Update production Django `.env` with same settings
   - Test with real students from level testing

2. **Monitor and Iterate**
   - Watch logs for errors: `docker compose logs -f`
   - Check monitoring dashboard
   - Review audit trail in logs

3. **Plan Migration**
   - Phase in modules one at a time
   - Disable legacy sync as modules migrate
   - Eventually remove adapter service

## 🆘 Troubleshooting

If something doesn't work:

1. **Check Service Health**
   ```bash
   curl https://legacy-adapter.vps.example.com/health
   ```

2. **View Logs**
   ```bash
   docker compose -f docker-compose.vps.yml logs --tail=100
   ```

3. **Verify Network**
   ```bash
   # From VPS
   telnet legacy-server.example.com 14433
   ```

4. **Test API Key**
   ```bash
   curl -H "X-API-Key: your-key" https://legacy-adapter.vps.example.com/students/12345
   ```

## 📖 Additional Resources

- [README.md](./README.md) - Complete service documentation
- [Django Integration Guide](./docs/DJANGO_INTEGRATION.md)
- [Troubleshooting Guide](./docs/TROUBLESHOOTING.md)

---

**Questions?** Check the logs, review the documentation, or create an issue in the project repository.

Happy migrating! 🚀
