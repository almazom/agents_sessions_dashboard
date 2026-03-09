#!/bin/bash
# Agent Nexus - Startup Script

set -e

cd /home/pets/temp/sessions_landing

echo "🚀 Запуск Agent Nexus..."

# Backend
echo "📦 Backend..."
cd backend
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Frontend (если установлен)
if [ -d "frontend/node_modules" ]; then
    echo "🎨 Frontend..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
fi

echo "✅ Agent Nexus запущен!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Нажмите Ctrl+C для остановки"

# Wait
trap "kill $BACKEND_PID ${FRONTEND_PID:-} 2>/dev/null" EXIT
wait
