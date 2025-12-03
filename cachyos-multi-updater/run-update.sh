#!/bin/bash
#
# CachyOS Multi-Updater - Update Wrapper
# Wrapper script to execute update-all.sh and keep terminal open
# Used by desktop files for reliable terminal persistence
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)
#
# This is free and open source software (FOSS).
# You are welcome to modify and distribute it under the terms of the MIT License.
#
# Repository: https://github.com/SunnyCueq/cachyos-multi-updater
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPDATE_SCRIPT="$SCRIPT_DIR/update-all.sh"
UPDATE_MODE="${1:-}"

# Führe das Update-Script aus
if [ -n "$UPDATE_MODE" ]; then
    "$UPDATE_SCRIPT" "$UPDATE_MODE"
else
    "$UPDATE_SCRIPT"
fi

EXIT_CODE=$?

# Terminal offen halten - IMMER
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Update erfolgreich abgeschlossen!"
else
    echo "❌ Update mit Fehler beendet (Exit-Code: $EXIT_CODE)"
fi
echo ""
read -r -p "Drücke Enter zum Beenden..." || sleep 5

exit $EXIT_CODE

