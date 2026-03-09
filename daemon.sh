#!/bin/bash
# Agent Nexus Daemon Starter
# Run this script to start the server

cd /home/pets/temp/sessions_landing

# Load environment
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Default port
PORT=${NEXUS_PORT:-18890}

# Kill existing
pkill -f "uvicorn backend.api.main" 2>/dev/null || true
sleep 2

# Start server
exec python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
