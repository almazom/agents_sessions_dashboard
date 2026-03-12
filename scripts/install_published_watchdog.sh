#!/bin/bash

set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_ROOT="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
SCRIPTS_DIR="${PROJECT_ROOT}/scripts"
TMP_CRON=$(mktemp)
trap 'rm -f "$TMP_CRON"' EXIT

existing_cron=$(crontab -l 2>/dev/null || true)

{
    printf "%s\n" "$existing_cron"
    printf "\n# >>> NEXUS_PUBLISHED_WATCHDOG_START\n"
    printf "@reboot %s/start_published.sh >> /tmp/nexus-watchdog.log 2>&1\n" "$SCRIPTS_DIR"
    printf "* * * * * %s/keep_alive.sh\n" "$SCRIPTS_DIR"
    printf "# <<< NEXUS_PUBLISHED_WATCHDOG_END\n"
} | awk '
    BEGIN { skip = 0 }
    /# >>> NEXUS_PUBLISHED_WATCHDOG_START/ { skip = 1; next }
    /# <<< NEXUS_PUBLISHED_WATCHDOG_END/ { skip = 0; next }
    skip == 0 { print }
' > "$TMP_CRON"

{
    printf "%s\n" "$(cat "$TMP_CRON")"
    printf "\n# >>> NEXUS_PUBLISHED_WATCHDOG_START\n"
    printf "@reboot %s/start_published.sh >> /tmp/nexus-watchdog.log 2>&1\n" "$SCRIPTS_DIR"
    printf "* * * * * %s/keep_alive.sh\n" "$SCRIPTS_DIR"
    printf "# <<< NEXUS_PUBLISHED_WATCHDOG_END\n"
} | crontab -

echo "Installed published watchdog cron entries"
