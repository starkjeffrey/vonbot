# MSSQL 2012 Connection Guide

**Critical configuration for connecting to legacy MSSQL 2012 with TLS 1.0/1.1**

## The Problem

Standard pymssql installations fail to connect to MSSQL 2012 servers because:

1. **MSSQL 2012 uses TLS 1.0/1.1** - Modern systems reject these deprecated protocols
2. **Pre-built FreeTDS packages don't support legacy TLS** - Must compile from source
3. **pymssql requires specific configuration** - Environment variables and settings must align

### Error Symptoms

```
DB-Lib error message 20002, severity 9:
Adaptive Server connection failed (96.9.90.64)
```

Or:

```
DB-Lib error message 20009, severity 9:
Unable to connect: Adaptive Server is unavailable or does not exist
Net-Lib error during Connection refused (111)
```

## The Solution

### 1. Compile FreeTDS from Source (Dockerfile)

**Critical compilation flags:**

```dockerfile
# Download and compile FreeTDS 1.3.17
RUN cd /tmp && \
    wget ftp://ftp.freetds.org/pub/freetds/stable/freetds-1.3.17.tar.gz && \
    tar -xzf freetds-1.3.17.tar.gz && \
    cd freetds-1.3.17 && \
    CFLAGS="-I/usr/include/openssl" \
    LDFLAGS="-L/usr/lib/x86_64-linux-gnu -L/usr/lib/aarch64-linux-gnu" \
    ./configure --prefix=/usr/local --with-openssl=/usr --enable-msdblib && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/freetds-1.3.17* && \
    ldconfig
```

**Why these flags?**
- `CFLAGS="-I/usr/include/openssl"` - Points to OpenSSL headers
- `LDFLAGS` - Points to OpenSSL libraries for both x86_64 and ARM64
- `--with-openssl=/usr` - Enables OpenSSL support
- `--enable-msdblib` - Enables MSSQL compatibility mode

### 2. Configure FreeTDS (freetds.conf)

**CRITICAL: Settings must be in [global] section:**

```ini
[global]
    # Global settings for ALL connections
    tds version = 7.3
    client charset = UTF-8
    text size = 64512
    dump file = /tmp/freetds.log
    debug flags = 0x0000

    # CRITICAL: Disable encryption globally for MSSQL 2012 compatibility
    # MSSQL 2012 uses TLS 1.0/1.1 which modern OpenSSL rejects
    encryption = off
    trust server certificate = yes

# Legacy MSSQL 2012 Server Configuration
[OLDSIS2]
    host = 96.9.90.64
    port = 1500
    tds version = 7.3
    trust server certificate = yes
    encryption = off
```

**Why `[global]` section?**
- pymssql doesn't always read named server configurations
- Global settings apply to ALL connections
- Ensures encryption is disabled regardless of connection method

### 3. Set Environment Variables (Dockerfile)

```dockerfile
# Set FreeTDS environment variables for pymssql
# CRITICAL: pymssql needs these to find the freetds.conf file
ENV FREETDSCONF=/usr/local/etc/freetds.conf
ENV TDSVER=7.3
```

**Why these environment variables?**
- `FREETDSCONF` - Tells pymssql where to find configuration
- `TDSVER` - Sets default TDS protocol version

### 4. Use Python 3.11 (Not 3.14)

```dockerfile
FROM python:3.11-slim
```

**Why Python 3.11?**
- pymssql 2.3.2 has dependency conflicts with Python 3.14
- setuptools_scm version incompatibilities
- Python 3.11 provides better overall compatibility

### 5. Connect with Direct Host:Port (database.py)

```python
import pymssql
from app.config import settings

conn = pymssql.connect(
    server=f"{settings.LEGACY_DB_HOST}:{settings.LEGACY_DB_PORT}",
    user=settings.LEGACY_DB_USER,
    password=settings.LEGACY_DB_PASSWORD,
    database=settings.LEGACY_DB_NAME,
    timeout=30,
    login_timeout=30,
    appname="LegacyAdapter",
    tds_version="7.3",  # CRITICAL: Must match freetds.conf
)
```

**Why not use named server (OLDSIS2)?**
- `tsql` command-line tool reads freetds.conf automatically
- pymssql requires environment variables + direct connection
- Using `server="OLDSIS2"` doesn't reliably work with pymssql
- Direct `host:port` is more explicit and predictable

## Verification Steps

### 1. Verify FreeTDS Configuration

```bash
docker compose -f docker-compose.local.yml exec legacy-adapter /usr/local/bin/tsql -C
```

**Expected output:**
```
freetds.conf directory: /usr/local/etc
OpenSSL: yes
TDS version: auto
```

### 2. Test with tsql Command

```bash
docker compose -f docker-compose.local.yml exec legacy-adapter bash -c '
echo "SELECT @@VERSION
GO
QUIT" | /usr/local/bin/tsql -S OLDSIS2 -U sa -P 123456
'
```

**Expected output:**
```
Microsoft SQL Server 2008 R2 (RTM) - 10.50.1600.1 (X64)
Enterprise Edition (64-bit) on Windows NT 6.2 <X64>
```

### 3. Test with pymssql

```bash
docker compose -f docker-compose.local.yml exec legacy-adapter python3 -c "
import pymssql
conn = pymssql.connect(
    server='96.9.90.64:1500',
    user='sa',
    password='123456',
    database='New_PUCDB',
    tds_version='7.3'
)
cursor = conn.cursor()
cursor.execute('SELECT @@VERSION')
print(cursor.fetchone()[0][:80])
cursor.close()
conn.close()
"
```

**Expected output:**
```
Microsoft SQL Server 2008 R2 (RTM) - 10.50.1600.1 (X64)
```

### 4. Test Health Endpoint

```bash
docker compose -f docker-compose.local.yml exec legacy-adapter curl http://localhost:8000/health
```

**Expected output:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-02T10:40:43.104432",
  "version": "1.0.0"
}
```

### 5. Query Test Data

```bash
docker compose -f docker-compose.local.yml exec legacy-adapter python3 -c "
import pymssql
conn = pymssql.connect(
    server='96.9.90.64:1500',
    user='sa',
    password='123456',
    database='New_PUCDB',
    tds_version='7.3'
)
cursor = conn.cursor()
cursor.execute('SELECT * FROM students WHERE id = %s', ('10774',))
row = cursor.fetchone()
print('Student found:', row[3] if row else 'Not found')
cursor.close()
conn.close()
"
```

## Troubleshooting

### Issue: "Adaptive Server connection failed"

**Cause:** Encryption is still enabled or TLS negotiation failing

**Fix:**
1. Check `encryption = off` is in `[global]` section of freetds.conf
2. Verify FREETDSCONF environment variable is set
3. Rebuild Docker image after changes

### Issue: "Server name not found in configuration files"

**Cause:** FreeTDS can't find freetds.conf or named server doesn't exist

**Fix:**
1. Verify file exists: `ls -la /usr/local/etc/freetds.conf`
2. Check FREETDSCONF environment variable
3. Use direct `host:port` connection instead of named server

### Issue: tsql works but pymssql doesn't

**Cause:** pymssql and tsql use different configuration lookup methods

**Fix:**
1. Ensure environment variables are set in Dockerfile (not just shell)
2. Use direct `host:port` connection string
3. Pass `tds_version="7.3"` explicitly in pymssql.connect()

### Issue: "Connection refused (111)"

**Cause:** Network routing issue or firewall blocking connection

**Fix:**
1. Test TCP connectivity: `nc -zv 96.9.90.64 1500`
2. Check if using correct network mode in docker-compose
3. Verify MSSQL server is listening on specified port

### Issue: Python 3.14 dependency conflicts

**Cause:** pymssql 2.3.2 has setuptools_scm incompatibilities with Python 3.14

**Fix:**
```dockerfile
FROM python:3.11-slim  # Not 3.14
```

## Key Learnings

### What DOESN'T Work

❌ Using pre-built `freetds-dev` apt package
❌ Relying on named servers in freetds.conf with pymssql
❌ Leaving encryption on (even if certificate trusted)
❌ Using Python 3.14
❌ Forgetting to set environment variables

### What DOES Work

✅ Compiling FreeTDS 1.3.17 from source with specific CFLAGS/LDFLAGS
✅ Setting `encryption = off` in `[global]` section
✅ Setting FREETDSCONF and TDSVER environment variables
✅ Using Python 3.11
✅ Direct `host:port` connection with `tds_version="7.3"`

## Security Considerations

### Why Disable Encryption?

MSSQL 2012 uses TLS 1.0/1.1 which are deprecated and rejected by modern systems. We must disable encryption entirely to connect.

**This is acceptable because:**
- Traffic is on private network (96.9.90.64 is internal)
- Database contains legacy data only (not sensitive production data)
- Temporary solution during migration period
- Alternative is blocking migration progress

**Mitigation:**
- Restrict MSSQL server to VPS IP only (Windows Firewall)
- Use API key authentication on adapter endpoints
- Disable adapter when migration complete

## Docker Compose Configuration

```yaml
legacy-adapter:
  build:
    context: ./services/legacy-adapter
    dockerfile: Dockerfile
  container_name: naga_v2_legacy_adapter
  restart: unless-stopped
  network_mode: "host"  # Access external MSSQL server
  env_file:
    - ./services/legacy-adapter/.env
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
    interval: 30s
    timeout: 10s
    retries: 3
  profiles:
    - legacy  # Optional service
```

## Environment Variables (.env)

```bash
# MSSQL Connection
LEGACY_DB_HOST=96.9.90.64
LEGACY_DB_PORT=1500
LEGACY_DB_USER=sa
LEGACY_DB_PASSWORD=123456
LEGACY_DB_NAME=New_PUCDB

# API Security
API_KEY=your-secure-api-key-here

# Development
DEBUG=true
```

## Build Process

```bash
# Build the image
docker compose -f docker-compose.local.yml --profile legacy build legacy-adapter

# Start the service
docker compose -f docker-compose.local.yml --profile legacy up legacy-adapter

# View logs
docker compose -f docker-compose.local.yml logs legacy-adapter -f
```

## Complete Working Example

```python
# app/database.py
import logging
import pymssql
from pymssql import Connection
from .config import settings

logger = logging.getLogger(__name__)

def get_connection() -> Connection:
    """Get database connection to MSSQL 2012 server."""
    try:
        logger.debug(
            "Creating connection to %s:%s/%s (using direct connection with freetds_conf)",
            settings.LEGACY_DB_HOST,
            settings.LEGACY_DB_PORT,
            settings.LEGACY_DB_NAME,
        )

        conn = pymssql.connect(
            server=f"{settings.LEGACY_DB_HOST}:{settings.LEGACY_DB_PORT}",
            user=settings.LEGACY_DB_USER,
            password=settings.LEGACY_DB_PASSWORD,
            database=settings.LEGACY_DB_NAME,
            timeout=30,
            login_timeout=30,
            appname="LegacyAdapter",
            tds_version="7.3",
        )

        logger.debug("Database connection established successfully")
        return conn

    except pymssql.Error as e:
        logger.error("Failed to connect to legacy database: %s", str(e))
        raise
```

## References

- [FreeTDS Documentation](https://www.freetds.org/userguide/)
- [pymssql Documentation](https://pymssql.readthedocs.io/)
- [TDS Protocol Versions](https://www.freetds.org/userguide/choosingtdsprotocol.html)
- [MSSQL 2012 TLS Support](https://docs.microsoft.com/en-us/troubleshoot/sql/connect/tls-1-2-support-microsoft-sql-server)

---

**Last Updated:** 2025-11-02
**Tested On:** Mac M2, Docker Desktop 4.x, Python 3.11
**MSSQL Version:** 2012 (10.50.1600.1)
**FreeTDS Version:** 1.3.17
