#!/bin/bash
# Agent Nexus - Keep Alive Script
# Запускать через cron каждые 5 минут: */5 * * * * /home/pets/temp/sessions_landing/keep_alive.sh

cd /home/pets/temp/sessions_landing

# Проверить запущен ли сервер
if ! pgrep -f "uvicorn backend.api.main" > /dev/null; then
    echo "$(date): Starting Nexus server..." >> /tmp/nexus-watchdog.log
    
    # Загрузить env
    export $(grep -v '^#' .env | xargs)
    
    # Запустить
    nohup python3 -m uvicorn backend.api.main:app \
        --host 0.0.0.0 \
        --port $NEXUS_PORT \
        > /tmp/nexus.log 2>&1 &
    
    echo "$(date): Server started on port $NEXUS_PORT" >> /tmp/nexus-watchdog.log
fi
