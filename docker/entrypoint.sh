#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════"
echo " 🤖 Universal AI Content OS v6.0.0"
echo "═══════════════════════════════════════════════════"

# Wait for PostgreSQL if configured
if [ -n "$POSTGRES_HOST" ]; then
    echo "⏳ Waiting for PostgreSQL at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
    for i in $(seq 1 30); do
        if python -c "
import socket
s = socket.socket()
try:
    s.settimeout(2)
    s.connect(('${POSTGRES_HOST}', ${POSTGRES_PORT:-5432}))
    print('PostgreSQL ready!')
except:
    exit(1)
finally:
    s.close()
" 2>/dev/null; then
            break
        fi
        echo "  Attempt $i/30..."
        sleep 2
    done
fi

# Wait for Redis if configured
if [ -n "$REDIS_HOST" ]; then
    echo "⏳ Waiting for Redis at $REDIS_HOST:${REDIS_PORT:-6379}..."
    for i in $(seq 1 15); do
        if python -c "
import socket
s = socket.socket()
try:
    s.settimeout(2)
    s.connect(('${REDIS_HOST}', ${REDIS_PORT:-6379}))
    print('Redis ready!')
except:
    exit(1)
finally:
    s.close()
" 2>/dev/null; then
            break
        fi
        sleep 1
    done
fi

echo ""
echo "🚀 Starting AI Content Operating System..."
echo "   Mode: ${APP_ENV:-development}"
echo ""

# Run the application
exec python main.py "$@"
