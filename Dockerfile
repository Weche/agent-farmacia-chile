# Multi-stage build for optimized Python deployment
FROM python:3.11-slim as builder

# Set environment variables for build optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies (this layer gets cached between builds)
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8080

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create app directory
WORKDIR /app

# Copy application code
COPY app ./app
COPY docs ./docs  
COPY templates ./templates
COPY data ./data
COPY .env.example ./

# Create data directory and backup location  
RUN mkdir -p /app/data /app/data_backup /app/data_source

# Backup vademecum file for volume copying
RUN cp /app/data/comprehensive_vademecum.csv /app/data_backup/ && \
    ls -la /app/data_backup/comprehensive_vademecum.csv

# Copy all Python modules and backup data to data_source (won't be overwritten by volume)
RUN cp -r /app/data/*.py /app/data_source/ && \
    cp /app/data/pharmacy_backup.json /app/data_source/ && \
    ls -la /app/data_source/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Ensure the data directory has proper permissions for the volume mount
RUN chmod 755 /app/data

# Create entrypoint script to handle volume permissions
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo 'echo "🚀 Starting Pharmacy Finder..."' >> /app/entrypoint.sh && \
    echo 'echo "📁 Ensuring volume permissions..."' >> /app/entrypoint.sh && \
    echo 'chmod 755 /app/data' >> /app/entrypoint.sh && \
    echo 'if [ ! -f "/app/data/comprehensive_vademecum.csv" ]; then' >> /app/entrypoint.sh && \
    echo '  echo "📋 Copying vademecum to volume..."' >> /app/entrypoint.sh && \
    echo '  if [ -f "/app/data_backup/comprehensive_vademecum.csv" ]; then' >> /app/entrypoint.sh && \
    echo '    cp /app/data_backup/comprehensive_vademecum.csv /app/data/comprehensive_vademecum.csv' >> /app/entrypoint.sh && \
    echo '    echo "✅ Vademecum copied from backup"' >> /app/entrypoint.sh && \
    echo '  else' >> /app/entrypoint.sh && \
    echo '    echo "❌ No vademecum backup found"' >> /app/entrypoint.sh && \
    echo '  fi' >> /app/entrypoint.sh && \
    echo 'fi' >> /app/entrypoint.sh && \
    echo 'echo "🗄️  Database path: $DATABASE_URL"' >> /app/entrypoint.sh && \
    echo 'echo "📋 Vademecum path: $VADEMECUM_PATH"' >> /app/entrypoint.sh && \
    echo 'echo "🏁 Starting application..."' >> /app/entrypoint.sh && \
    echo 'exec "$@"' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Expose port (matching fly.toml)
EXPOSE 8080

# Use entrypoint script for proper volume setup
ENTRYPOINT ["/app/entrypoint.sh"]

# Optimized startup command  
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
