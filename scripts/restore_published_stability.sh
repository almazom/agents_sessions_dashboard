#!/bin/bash

set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_ROOT="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
SCRIPTS_DIR="${PROJECT_ROOT}/scripts"

cd "$PROJECT_ROOT"
source "$PROJECT_ROOT/config/runtime.sh"
load_runtime_config

latest_summary_path() {
    local root=$1

    if [ ! -d "$root" ]; then
        return 0
    fi

    find "$root" -maxdepth 2 -name 'summary.json' -printf '%T@ %p\n' 2>/dev/null \
        | sort -nr \
        | head -n 1 \
        | cut -d' ' -f2-
}

run_step() {
    local label=$1
    shift

    echo ""
    echo "==> $label"
    "$@"
}

SMOKE_BEFORE=$(latest_summary_path "$PROJECT_ROOT/tmp/e2e-smoke")
CONFIDENCE_BEFORE=$(latest_summary_path "$PROJECT_ROOT/tmp/e2e-confidence")

run_step "Rebuild and restart published stack" "$SCRIPTS_DIR/start_published.sh"

run_step "Verify published visual smoke with screenshots" bash -lc "
    cd '$PROJECT_ROOT/frontend'
    npm run smoke:published:visual '$NEXUS_PUBLIC_URL'
"

run_step "Verify repeated diagnostics confidence" bash -lc "
    cd '$PROJECT_ROOT/frontend'
    NEXUS_E2E_PIPELINE_MODE=smoke npm run confidence:published:visual '$NEXUS_PUBLIC_URL'
"

SMOKE_AFTER=$(latest_summary_path "$PROJECT_ROOT/tmp/e2e-smoke")
CONFIDENCE_AFTER=$(latest_summary_path "$PROJECT_ROOT/tmp/e2e-confidence")

echo ""
echo "Published stability pipeline passed"
echo "  Public URL: $NEXUS_PUBLIC_URL"
if [ -n "$SMOKE_AFTER" ] && [ "$SMOKE_AFTER" != "$SMOKE_BEFORE" ]; then
    echo "  Smoke summary: $SMOKE_AFTER"
fi
if [ -n "$CONFIDENCE_AFTER" ] && [ "$CONFIDENCE_AFTER" != "$CONFIDENCE_BEFORE" ]; then
    echo "  Confidence summary: $CONFIDENCE_AFTER"
fi
echo "  Logs:"
echo "    /tmp/nexus-backend.log"
echo "    /tmp/nexus-frontend.log"
echo "    /tmp/nexus-frontend-build.log"
echo "    /tmp/nexus-caddy.log"
