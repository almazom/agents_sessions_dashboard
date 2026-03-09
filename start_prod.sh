#!/bin/bash
# Agent Nexus - Production Start
# Usage: ./start_prod.sh [PASSWORD]

set -e

cd /home/pets/temp/sessions_landing

# Порт из конфига или аргумент
PORT=${NEXUS_PORT:-18888}
PASSWORD=${1:-${NEXUS_PASSWORD:-""}}

export NEXUS_PASSWORD="$PASSWORD"
export NEXUS_IP_WHITELIST=""

echo "🚀 Agent Nexus"
echo "   Port: $PORT"
echo "   Password: ${PASSWORD:+✅ Set} ${PASSWORD:-❌ No password!}"
echo ""

# Остановить старый процесс
pkill -f "uvicorn backend.api.main:app" 2>/dev/null || true
sleep 1

# Запуск
exec python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
