# Legacy Adapter Service Dockerfile
# Platform: linux/amd64 for pymssql compatibility
# Python 3.11-slim for better pymssql compatibility

FROM python:3.11-slim

# Install build dependencies for FreeTDS compilation from source
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    curl \
    wget \
    gnupg \
    unixodbc-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Compile FreeTDS from source with OpenSSL support for MSSQL 2012 (TLS 1.0/1.1)
# Using CFLAGS/LDFLAGS that enable legacy TLS versions
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

WORKDIR /app

# Copy FreeTDS configuration for MSSQL 2012 compatibility
# FreeTDS looks in /usr/local/etc by default (as shown by tsql -C)
COPY freetds.conf /usr/local/etc/freetds.conf

# Set FreeTDS environment variables for pymssql
# CRITICAL: pymssql needs these to find the freetds.conf file
ENV FREETDSCONF=/usr/local/etc/freetds.conf
ENV TDSVER=7.3

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove wget \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY app/ ./app/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
