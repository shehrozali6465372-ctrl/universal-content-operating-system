# ─── Universal AI Content Operating System ───
# Multi-stage build for production

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

# Create non-root user
RUN groupadd -r aios && useradd -r -g aios -d /app -s /sbin/nologin aios

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create data directory for SQLite persistence
RUN mkdir -p data output/images && chown -R aios:aios /app

# Switch to non-root user
USER aios

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import json,subprocess; r=subprocess.run(['python','main.py','--status'],capture_output=True,text=True,timeout=5); d=json.loads(r.stdout); exit(0 if d.get('layers',0)>0 else 1)"

# Default command
CMD ["python", "main.py"]
