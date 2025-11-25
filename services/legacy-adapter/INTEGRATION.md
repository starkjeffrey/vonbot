# Legacy Adapter Integration Guide

## How Dependencies Get Installed

The legacy adapter is a **separate service** with its own container and dependencies.

### Architecture

```
┌─────────────────────────────────────┐
│ Django Container                    │
│ - Python 3.14 + Django              │
│ - Uses: backend/pyproject.toml      │
│ - Package manager: uv               │
└─────────────────────────────────────┘
         ↓ HTTP API calls
┌─────────────────────────────────────┐
│ Legacy Adapter Container            │
│ - Python 3.11 + FastAPI             │
│ - Uses: services/legacy-adapter/    │
│         requirements.txt            │
│ - Package manager: pip              │
└─────────────────────────────────────┘
```

### Installation Process

**Automatic via Docker Compose:**

1. When you run `docker compose --profile legacy up`, Docker:
   - Reads `docker-compose.local.yml`
   - Sees the `legacy-adapter` service definition
   - Builds the container using `services/legacy-adapter/Dockerfile`
   - Runs `pip install -r requirements.txt` INSIDE the container
   - Starts the FastAPI service on port 8002

**NO manual installation needed!** Docker handles everything.

## Usage

### Start Development Environment

```bash
# WITHOUT legacy adapter (normal development)
docker compose -f docker-compose.local.yml up

# WITH legacy adapter (when syncing to MSSQL)
docker compose -f docker-compose.local.yml --profile legacy up
```

### Service Endpoints

- **Django API**: http://localhost:8001
- **Legacy Adapter**: http://localhost:8002
- **Legacy Adapter Health**: http://localhost:8002/health
- **Legacy Adapter Docs**: http://localhost:8002/docs (when DEBUG=true)

### Configuration

**Django (.envs/.local/.django):**
```bash
LEGACY_SYNC_ENABLED=true
LEGACY_ADAPTER_URL=http://legacy-adapter:8001  # Internal Docker network
LEGACY_ADAPTER_API_KEY=your-api-key-here
```

**Legacy Adapter (services/legacy-adapter/.env):**
```bash
LEGACY_DB_HOST=your-mssql-server.com
LEGACY_DB_PORT=14433
LEGACY_DB_USER=sa
LEGACY_DB_PASSWORD=your-password
LEGACY_DB_NAME=naga_legacy
API_KEY=your-api-key-here
DEBUG=true
```

## How Django Communicates with Legacy Adapter

**Django never imports legacy adapter code.** Communication is purely via HTTP:

```python
# Django code example
import httpx
from django.conf import settings

async def sync_student_to_legacy(student):
    """Send student data to legacy MSSQL via adapter API."""
    if not settings.LEGACY_SYNC_ENABLED:
        return

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.LEGACY_ADAPTER_URL}/students",
            json={
                "student_id": student.student_id,
                "first_name": student.person.first_name,
                "last_name": student.person.last_name,
                # ... more fields
            },
            headers={"X-API-Key": settings.LEGACY_ADAPTER_API_KEY},
        )
        response.raise_for_status()
```

## Benefits of This Architecture

✅ **Isolated Dependencies**: FastAPI deps don't conflict with Django deps
✅ **Mac M2 Compatible**: pymssql builds in Linux container (no Mac build issues)
✅ **Security**: Django never has MSSQL credentials
✅ **Scalability**: Can deploy/scale independently
✅ **Easy Migration**: Disable with `LEGACY_SYNC_ENABLED=false` when done

## Troubleshooting

### Legacy adapter won't start

**Check if .env file exists:**
```bash
ls -la services/legacy-adapter/.env
```

**View logs:**
```bash
docker compose -f docker-compose.local.yml logs legacy-adapter -f
```

### Can't connect to MSSQL from adapter

**Test connection from within container:**
```bash
docker compose -f docker-compose.local.yml exec legacy-adapter bash
apt-get update && apt-get install -y telnet
telnet YOUR_MSSQL_HOST 14433
```

### API returns 401 Unauthorized

**Verify API key matches:**
```bash
# Check Django setting
grep LEGACY_ADAPTER_API_KEY backend/.envs/.local/.django

# Check adapter setting
grep API_KEY backend/services/legacy-adapter/.env
```

## Development Workflow

### Adding New Legacy Sync Features

1. **Update Django model/signal**
2. **Test with legacy adapter running locally**
3. **Verify data in MSSQL**
4. **Deploy adapter to VPS** (when ready)

### Testing Locally

```bash
# Terminal 1: Start all services with legacy adapter
cd backend
docker compose -f docker-compose.local.yml --profile legacy up

# Terminal 2: Run Django tests
docker compose -f docker-compose.local.yml exec django pytest

# Terminal 3: Test API directly
curl http://localhost:8002/health
```

## When to Enable Legacy Adapter

**Enable during:**
- Local testing of legacy sync features
- Integration testing with MSSQL
- Migration of legacy data

**Disable during:**
- Normal feature development (not touching legacy code)
- Running tests that don't need MSSQL
- When MSSQL server is unavailable

## Future: Removing Legacy Adapter

When migration is complete:

1. Set `LEGACY_SYNC_ENABLED=false` in Django
2. Remove `--profile legacy` from docker compose commands
3. (Optional) Remove `legacy-adapter` service from `docker-compose.local.yml`
4. Archive `services/legacy-adapter/` directory
5. Celebrate! 🎉