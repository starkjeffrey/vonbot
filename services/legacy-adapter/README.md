# Legacy MSSQL Adapter Service

**Secure REST API bridge between Django SIS and legacy MSSQL 2012 database**

## 🎯 Purpose

This service provides a secure, isolated layer for accessing the legacy MSSQL 2012 database during the phased SIS migration. It solves several critical problems:

1. **Security Isolation**: Protects legacy database with sa/123456 credentials
2. **Mac M2 Compatibility**: Runs pymssql in Linux container (no Mac build issues)
3. **Clean Architecture**: Django stays ignorant of MSSQL complexity
4. **Feature Flags**: Easy to disable legacy sync as modules migrate
5. **Audit Trail**: Complete logging of all legacy database operations

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│ Django (Mac M2 / VPS)              │
│ - Source of truth for data         │
│ - Generates student IDs            │
│ - PostgreSQL only                  │
└──────────────┬──────────────────────┘
               │
               │ HTTPS + API Key
               │
┌──────────────▼──────────────────────┐
│ Legacy Adapter (VPS Linux)         │
│ - FastAPI REST service             │
│ - Schema mapping layer             │
│ - Security & rate limiting         │
└──────────────┬──────────────────────┘
               │
               │ TDS/pymssql
               │
┌──────────────▼──────────────────────┐
│ Legacy MSSQL 2012 (Windows)        │
│ - Locked to VPS IP only            │
│ - No public internet access        │
└─────────────────────────────────────┘
```

## 🚀 Quick Start

### Test Locally (Mac M2)

```bash
# 1. Navigate to adapter directory
cd backend/services/legacy-adapter

# 2. Create .env file
cp .env.example .env

# 3. Edit .env with your MSSQL connection details
nano .env

# 4. Run test script
./scripts/test-local.sh

# 5. Test API endpoints
./scripts/test-api.sh your-api-key
```

### Deploy to VPS

```bash
# 1. Copy service files to VPS
scp -r backend/services/legacy-adapter user@vps.example.com:~/

# 2. SSH into VPS
ssh user@vps.example.com

# 3. Navigate to adapter directory
cd ~/legacy-adapter

# 4. Create and configure .env
cp .env.example .env
nano .env

# 5. Run deployment script
./scripts/deploy-vps.sh

# 6. Set up SSL (see DEPLOYMENT.md)
```

## 📁 Project Structure

```
legacy-adapter/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Settings from environment
│   ├── models.py        # Pydantic request/response models
│   ├── mappers.py       # Django ↔ Legacy schema mapping
│   └── database.py      # MSSQL connection management
├── scripts/
│   ├── test-local.sh    # Test on Mac M2
│   ├── deploy-vps.sh    # Deploy to VPS
│   ├── lockdown-mssql.ps1  # Windows firewall script
│   ├── monitor.sh       # Health monitoring
│   └── test-api.sh      # API endpoint tests
├── tests/
│   └── test_students.py
├── Dockerfile
├── docker-compose.dev.yml     # Local development (Mac M2)
├── docker-compose.vps.yml     # VPS deployment
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Configuration

### Environment Variables

**Required:**
- `LEGACY_DB_HOST` - MSSQL server hostname/IP
- `LEGACY_DB_USER` - Database username (e.g., sa)
- `LEGACY_DB_PASSWORD` - Database password
- `LEGACY_DB_NAME` - Database name
- `API_KEY` - Secure API key (generate with `openssl rand -hex 32`)

**Optional:**
- `LEGACY_DB_PORT` - Database port (default: 1433)
- `ALLOWED_ORIGINS` - CORS origins (default: http://localhost:8000)
- `RATE_LIMIT_PER_MINUTE` - Rate limit (default: 60)
- `DEBUG` - Enable debug mode (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)

### Django Configuration

Add to `backend/.env`:

```bash
# Legacy adapter configuration
LEGACY_SYNC_ENABLED=true
LEGACY_ADAPTER_URL=https://legacy-adapter.vps.example.com
LEGACY_ADAPTER_API_KEY=your-generated-api-key-here
```

## 🔒 Security Features

1. **API Key Authentication**: X-API-Key header required for all endpoints
2. **Rate Limiting**: 60 requests/minute per IP (configurable)
3. **CORS Protection**: Restricted to configured origins
4. **Request Logging**: Complete audit trail of all operations
5. **Network Isolation**: MSSQL server locked to VPS IP only

### Windows Firewall Lockdown

Run this on the Windows 11 machine hosting MSSQL:

```powershell
# Run PowerShell as Administrator
.\scripts\lockdown-mssql.ps1 -VpsIP "YOUR_VPS_IP" -MssqlPort 14433

# Dry run first to verify:
.\scripts\lockdown-mssql.ps1 -VpsIP "YOUR_VPS_IP" -MssqlPort 14433 -DryRun
```

This configures Windows Firewall to ONLY allow your VPS IP to access MSSQL.

## 📊 API Documentation

### Endpoints

**Health Check** (No auth required)
```bash
GET /health
```

**Create Student**
```bash
POST /students
Headers:
  X-API-Key: your-api-key
  Content-Type: application/json

Body:
{
  "student_id": 12345,
  "first_name": "Sopheak",
  "last_name": "Chan",
  "date_of_birth": "2000-01-15",
  "gender": "M",
  "is_monk": false,
  ...
}
```

**Get Student**
```bash
GET /students/{student_id}
Headers:
  X-API-Key: your-api-key
```

**Soft Delete Student**
```bash
DELETE /students/{student_id}
Headers:
  X-API-Key: your-api-key
```

### Interactive Docs

When `DEBUG=true`, API docs are available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 🧪 Testing

### Test Local Service

```bash
# Start service and run health checks
./scripts/test-local.sh

# Test API endpoints with sample data
./scripts/test-api.sh your-api-key

# Monitor service health
./scripts/monitor.sh 30  # Check every 30 seconds
```

### Run Python Tests

```bash
# TODO: Add pytest tests
pytest tests/
```

## 🔍 Monitoring

### Health Check

```bash
curl http://localhost:8001/health
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

### View Logs

```bash
# Local development
docker compose -f docker-compose.dev.yml logs -f

# VPS deployment
docker compose -f docker-compose.vps.yml logs -f

# Follow specific number of lines
docker compose -f docker-compose.vps.yml logs --tail=100 -f
```

## 🐛 Troubleshooting

### Service Won't Start

1. Check Docker is running: `docker ps`
2. Check .env file exists and is valid
3. View logs: `docker compose logs`
4. Verify MSSQL connection: `telnet MSSQL_HOST MSSQL_PORT`

### Cannot Connect to MSSQL

1. Verify Windows firewall allows VPS IP
2. Check MSSQL is listening on configured port
3. Test from VPS: `telnet legacy-server.com 14433`
4. Check MSSQL credentials in .env

### API Returns 401 Unauthorized

1. Verify API_KEY in adapter .env matches Django setting
2. Check X-API-Key header is being sent
3. Verify no typos in API key

### Rate Limit Errors (429)

1. Check RATE_LIMIT_PER_MINUTE setting
2. Review logs for source of excessive requests
3. Increase limit if legitimate traffic

## 📈 Performance

### Resource Requirements

**Minimum:**
- 256MB RAM
- 0.25 CPU
- 1GB disk

**Recommended:**
- 512MB RAM
- 0.5 CPU
- 2GB disk

### Scaling

For high traffic:
1. Run multiple instances behind load balancer
2. Use Redis for rate limiting (shared state)
3. Implement connection pooling for MSSQL

## 🗺️ Migration Roadmap

### Phase 1: Testing (Week 1-2)
- ✅ Deploy adapter to VPS
- ✅ Test with sample data
- ✅ Verify Django integration
- ✅ Lock down Windows firewall

### Phase 2: Pilot (Week 3-4)
- Enable for level_testing app only
- Monitor for errors
- Collect performance metrics

### Phase 3: Rollout (Month 2)
- Enable for all modules
- Full dual-write operation
- Monitor data consistency

### Phase 4: Wind Down (Month 3+)
- Disable sync for migrated modules
- Eventually set LEGACY_SYNC_ENABLED=false
- Remove adapter service
- Decommission legacy MSSQL

## 📚 Additional Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Detailed deployment guide
- [Django Integration Example](./docs/DJANGO_INTEGRATION.md)
- [API Schema Reference](./docs/API_SCHEMA.md)

## 🙏 Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [pymssql](https://pymssql.readthedocs.io/) - MSSQL database driver
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [uvicorn](https://www.uvicorn.org/) - ASGI server

## 📄 License

Part of Naga University Student Information System. Internal use only.
