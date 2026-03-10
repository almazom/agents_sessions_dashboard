#!/bin/bash
# Agent Nexus Daemon Starter
# Run this script to start the server

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_ROOT="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

cd "$PROJECT_ROOT"
source "$PROJECT_ROOT/config/runtime.sh"
load_runtime_config

# Kill existing
pkill -f "uvicorn backend.api.main" 2>/dev/null || true
sleep "$NEXUS_PROCESS_STOP_WAIT_SECONDS"

# Start server
exec python3 -m uvicorn backend.api.main:app --host "$NEXUS_HOST" --port "$NEXUS_BACKEND_PORT"
