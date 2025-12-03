#!/bin/bash
#
# CachyOS Multi-Updater - Desktop Shortcut Creator
# Helper script to create desktop shortcuts for update-all.sh
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
SCRIPT_PATH="$SCRIPT_DIR/update-all.sh"
DESKTOP_FILE="$SCRIPT_DIR/update-all.desktop"
TARGET_DIR="${1:-$HOME/Schreibtisch}"
UPDATE_MODE="${2:-}"  # Optional: --dry-run, --interactive, --auto

# Prüfe ob Script existiert
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Fehler: update-all.sh nicht gefunden in $SCRIPT_DIR" >&2
    exit 1
fi

# Erstelle Desktop-Datei mit absolutem Pfad
# WICHTIG: Verwende Wrapper-Script run-update.sh für zuverlässiges Terminal offen halten
# Für KDE/Plasma: konsole -e mit Wrapper-Script

WRAPPER_SCRIPT="$SCRIPT_DIR/run-update.sh"

# Prüfe ob Wrapper-Script existiert, sonst erstelle es
if [ ! -f "$WRAPPER_SCRIPT" ]; then
    echo "⚠️  Wrapper-Script nicht gefunden, erstelle es..." >&2
    cat > "$WRAPPER_SCRIPT" <<'WRAPPER_EOF'
#!/bin/bash
# Wrapper-Script zum Ausführen von update-all.sh mit Terminal offen halten
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPDATE_SCRIPT="$SCRIPT_DIR/update-all.sh"
UPDATE_MODE="${1:-}"
if [ -n "$UPDATE_MODE" ]; then
    "$UPDATE_SCRIPT" "$UPDATE_MODE"
else
    "$UPDATE_SCRIPT"
fi
EXIT_CODE=$?
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
WRAPPER_EOF
    chmod +x "$WRAPPER_SCRIPT"
fi

# Baue Exec-String mit Wrapper-Script und optionalem Update-Modus
# WICHTIG: Desktop-Dateien haben Probleme mit Escaping - verwende temporäres Script
# WICHTIG: --auto ist kein gültiger Parameter für update-all.sh (Standard-Modus ist automatisch)
# Erstelle ein temporäres Script, das die Parameter bereits enthält
LAUNCHER_SCRIPT="$SCRIPT_DIR/launch-update.sh"

# Konvertiere --auto zu leerem String (Standard-Modus = automatisch)
if [ "$UPDATE_MODE" = "--auto" ]; then
    UPDATE_MODE=""
fi

if [ -n "$UPDATE_MODE" ]; then
    cat > "$LAUNCHER_SCRIPT" <<LAUNCHER_EOF
#!/bin/bash
exec "$WRAPPER_SCRIPT" "$UPDATE_MODE"
LAUNCHER_EOF
else
    cat > "$LAUNCHER_SCRIPT" <<LAUNCHER_EOF
#!/bin/bash
exec "$WRAPPER_SCRIPT"
LAUNCHER_EOF
fi
chmod +x "$LAUNCHER_SCRIPT"

# Verwende konsole --hold - das hält das Terminal explizit offen
# WICHTIG: Pfade mit Leerzeichen/Klammern müssen in Desktop-Dateien in Anführungszeichen
EXEC_CMD="konsole --hold -e \"$LAUNCHER_SCRIPT\""

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=Update All
Comment=Ein-Klick-Update für CachyOS + AUR + Cursor + AdGuard
Exec=$EXEC_CMD
Icon=system-software-update
Terminal=false
Type=Application
Categories=System;
EOF

echo "✅ Desktop-Datei erstellt: $DESKTOP_FILE"
echo "   Script-Pfad: $SCRIPT_PATH"

# Kopiere auf Desktop falls gewünscht
if [ -d "$TARGET_DIR" ]; then
    cp "$DESKTOP_FILE" "$TARGET_DIR/"
    chmod +x "$TARGET_DIR/update-all.desktop"
    echo "✅ Desktop-Verknüpfung erstellt: $TARGET_DIR/update-all.desktop"
else
    echo "⚠️  Ziel-Verzeichnis nicht gefunden: $TARGET_DIR"
    echo "   Desktop-Datei wurde nur im Script-Verzeichnis erstellt"
fi

echo ""
echo "Verwendung:"
echo "  - Im Script-Verzeichnis: $DESKTOP_FILE"
echo "  - Auf Desktop: $TARGET_DIR/update-all.desktop (falls kopiert)"

