# ─── Universal AI Content Operating System ───
# Multi-stage production build v6.0.0
# ────────────────────────────────────────────

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Security: non-root user
RUN groupadd -r aios && useradd -r -g aios -d /app -s /sbin/nologin aios

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

# Create persistent directories
RUN mkdir -p data output/images logs backups \
    && chown -R aios:aios /app

# Entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    APP_PORT=8000

USER aios
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || python main.py --status > /dev/null 2>&1

ENTRYPOINT ["tini", "--"]
CMD ["/entrypoint.sh"]
