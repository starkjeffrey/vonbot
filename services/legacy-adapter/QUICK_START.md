# Legacy Adapter Quick Start

**TL;DR** - Commands you'll actually use

## 🚀 Local Development (Mac M2)

```bash
cd backend/services/legacy-adapter

# First time setup
cp .env.example .env
nano .env  # Add your MSSQL connection details

# Start service
docker compose -f docker-compose.dev.yml up -d

# Check status
docker compose -f docker-compose.dev.yml ps

# View logs
docker compose -f docker-compose.dev.yml logs -f

# Stop service
docker compose -f docker-compose.dev.yml down

# Rebuild after code changes
docker compose -f docker-compose.dev.yml up -d --build
```

## 🌐 VPS Deployment

```bash
# On VPS
cd ~/legacy-adapter

# First time setup
cp .env.example .env
nano .env  # Add your MSSQL connection details

# Deploy
./scripts/deploy-vps.sh

# Or manually:
docker compose -f docker-compose.vps.yml up -d --build

# View logs
docker compose -f docker-compose.vps.yml logs -f

# Restart
docker compose -f docker-compose.vps.yml restart

# Stop
docker compose -f docker-compose.vps.yml down
```

## 🧪 Testing

```bash
# Test local service
./scripts/test-local.sh

# Test API endpoints
./scripts/test-api.sh your-api-key

# Monitor health
./scripts/monitor.sh 30  # Check every 30 seconds

# Manual health check
curl http://localhost:8001/health
```

## 🔐 Security Setup

```powershell
# On Windows 11 (as Administrator)
cd C:\path\to\legacy-adapter\scripts

# Dry run first
.\lockdown-mssql.ps1 -VpsIP "YOUR_VPS_IP" -MssqlPort 14433 -DryRun

# Apply for real
.\lockdown-mssql.ps1 -VpsIP "YOUR_VPS_IP" -MssqlPort 14433
```

## 📝 Django Configuration

Add to `backend/.env`:

```bash
LEGACY_SYNC_ENABLED=true
LEGACY_ADAPTER_URL=https://legacy-adapter.vps.example.com
LEGACY_ADAPTER_API_KEY=your-generated-api-key
```

## 🐛 Troubleshooting

```bash
# Check if service is responding
curl http://localhost:8001/health

# Check container status
docker compose -f docker-compose.dev.yml ps

# View recent logs
docker compose -f docker-compose.dev.yml logs --tail=50

# Restart service
docker compose -f docker-compose.dev.yml restart

# Full rebuild
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d --build --no-cache
```

## ⚙️ Common Tasks

### Generate API Key
```bash
openssl rand -hex 32
```

### Test MSSQL Connection
```bash
# From VPS
telnet legacy-server.example.com 14433
```

### View Live Logs
```bash
docker compose -f docker-compose.dev.yml logs -f | grep -E "(ERROR|WARN|✅|❌)"
```

### Check Service Resources
```bash
docker stats legacy_adapter_local
```

## 📂 File Naming

- **`docker-compose.dev.yml`** - Local development (Mac M2)
  - Named `.dev.yml` to avoid conflict with backend's `docker-compose.local.yml`

- **`docker-compose.vps.yml`** - VPS production deployment

## 🔗 Quick Links

- **Local Service:** http://localhost:8001
- **Local API Docs:** http://localhost:8001/docs (if DEBUG=true)
- **Health Check:** http://localhost:8001/health

## 📚 More Info

- Full docs: [README.md](./README.md)
- Step-by-step guide: [GETTING_STARTED.md](./GETTING_STARTED.md)
