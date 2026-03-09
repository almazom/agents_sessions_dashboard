#!/bin/bash
# Agent Nexus - Start Daemon
# Запускает сервер в фоне с nohup

set -e

cd /home/pets/temp/sessions_landing

# Загрузить .env
set -a
source .env 2>/dev/null || true
set +a

# Остановить старые процессы
pkill -f "uvicorn backend.api.main:app" 2>/dev/null || true
sleep 2

# Проверить порт
if lsof -i:18888 >/dev/null 2>&1; then
    echo "❌ Порт 18888 занят"
    lsof -i:18888
    exit 1
fi

echo "🚀 Agent Nexus"
echo "   URL: http://0.0.0.0:18888"
echo "   Password: ✅ Set from .env"
echo ""

# Запуск с nohup
nohup python3 -m uvicorn backend.api.main:app \
    --host 0.0.0.0 \
    --port 18888 \
    > /tmp/nexus.log 2>&1 &

NEXUS_PID=$!
echo "PID: $NEXUS_PID"

# Сохранить PID
echo $NEXUS_PID > /tmp/nexus.pid

sleep 5

# Проверка
if curl -s http://localhost:18888/health >/dev/null 2>&1; then
    echo "✅ Server running!"
    echo ""
    echo "🌐 URLs:"
    echo "   Local:  http://localhost:18888"
    echo "   Global: http://107.174.231.22:18888"
    echo "   API:    http://107.174.231.22:18888/api/docs"
    echo ""
    echo "📝 Logs: tail -f /tmp/nexus.log"
else
    echo "❌ Server failed to start"
    echo ""
    cat /tmp/nexus.log
fi
