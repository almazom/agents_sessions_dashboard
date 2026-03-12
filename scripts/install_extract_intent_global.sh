#!/usr/bin/env bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
SOURCE_PATH="${SCRIPT_DIR}/extract-intent"
TARGET_DIR="${HOME}/.local/bin"
TARGET_PATH="${TARGET_DIR}/extract-intent"

mkdir -p "$TARGET_DIR"
rm -f "$TARGET_PATH"
install -m 755 "$SOURCE_PATH" "$TARGET_PATH"
echo "Installed $TARGET_PATH"
