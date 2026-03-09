#!/bin/bash
# Agent Nexus - Production Start
# Usage: ./run.sh

set -e

cd /home/pets/temp/sessions_landing

# Load .env
if [ -f .env ]; then
    echo "📁 Загрузка .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Вывод конфигурации (без пароля!)
echo "🚀 Agent Nexus"
echo "   Host: ${NEXUS_HOST:-0.0.0.0}"
echo "   Port: ${NEXUS_PORT:-18888}"
echo "   Password: ${NEXUS_PASSWORD:+✅ Установлен}"
echo "   DB: ${NEXUS_DB_PATH:-~/.nexus/nexus.db}"
echo ""

# Остановить старый процесс
pkill -f "uvicorn backend.api.main:app" 2>/dev/null || true
sleep 2

# Запуск
exec python3 -m uvicorn backend.api.main:app \
    --host ${NEXUS_HOST:-0.0.0.0} \
    --port ${NEXUS_PORT:-18888}
