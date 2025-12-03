#!/bin/bash
#
# CachyOS Multi-Updater - Setup Script
# Interactive setup script for first-time installation
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
DESKTOP_HELPER="$SCRIPT_DIR/create-desktop-shortcut.sh"

# Farben für Ausgabe
if [ -t 1 ]; then
    COLOR_BOLD='\033[1m'
    COLOR_SUCCESS='\033[0;32m'
    COLOR_INFO='\033[0;34m'
    COLOR_WARNING='\033[0;33m'
    COLOR_ERROR='\033[0;31m'
    COLOR_RESET='\033[0m'
else
    COLOR_BOLD=''
    COLOR_SUCCESS=''
    COLOR_INFO=''
    COLOR_WARNING=''
    COLOR_ERROR=''
    COLOR_RESET=''
fi

echo -e "${COLOR_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
echo -e "${COLOR_BOLD}🚀 CachyOS Multi-Updater Setup${COLOR_RESET}"
echo -e "${COLOR_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
echo ""

# Prüfe ob update-all.sh existiert
if [ ! -f "$UPDATE_SCRIPT" ]; then
    echo -e "${COLOR_ERROR}❌ Fehler: update-all.sh nicht gefunden in $SCRIPT_DIR${COLOR_RESET}" >&2
    exit 1
fi

# Mache Script ausführbar
chmod +x "$UPDATE_SCRIPT" 2>/dev/null || true
if [ -f "$DESKTOP_HELPER" ]; then
    chmod +x "$DESKTOP_HELPER" 2>/dev/null || true
fi

# Frage nach Update-Modus
echo -e "${COLOR_INFO}📋 Wähle Update-Modus:${COLOR_RESET}"
echo ""
echo "  1) --dry-run      (Test-Modus, keine Änderungen)"
echo "  2) --interactive   (Interaktive Auswahl der Komponenten)"
echo "  3) Standard        (Automatisch, alle Updates)"
echo ""
read -r -p "Wähle Modus (1-3, Standard: 3): " mode_choice
mode_choice=${mode_choice:-3}

case "$mode_choice" in
    1)
        UPDATE_MODE="--dry-run"
        MODE_NAME="Test-Modus"
        ;;
    2)
        UPDATE_MODE="--interactive"
        MODE_NAME="Interaktiv"
        ;;
    3)
        UPDATE_MODE=""  # Standard-Modus = kein Parameter
        MODE_NAME="Automatisch (Standard)"
        ;;
    *)
        UPDATE_MODE=""  # Standard-Modus = kein Parameter
        MODE_NAME="Automatisch (Standard)"
        echo -e "${COLOR_WARNING}⚠️  Ungültige Eingabe, verwende Standard (automatisch)${COLOR_RESET}"
        ;;
esac

echo ""
echo -e "${COLOR_SUCCESS}✅ Gewählter Modus: $MODE_NAME${COLOR_RESET}"
echo ""

# Frage nach Desktop-Verknüpfung
read -r -p "Desktop-Verknüpfung erstellen? (j/N): " create_desktop
create_desktop=${create_desktop:-n}

if [[ "$create_desktop" =~ ^[jJyY]$ ]]; then
    echo ""
    echo -e "${COLOR_INFO}📝 Erstelle Desktop-Verknüpfung...${COLOR_RESET}"
    
    if [ -f "$DESKTOP_HELPER" ]; then
        # Erstelle Desktop-Verknüpfung mit gewähltem Modus
        if bash "$DESKTOP_HELPER" "$HOME/Schreibtisch" "$UPDATE_MODE" 2>/dev/null; then
            echo -e "${COLOR_SUCCESS}✅ Desktop-Verknüpfung erstellt${COLOR_RESET}"
        else
            echo -e "${COLOR_WARNING}⚠️  Desktop-Verknüpfung konnte nicht erstellt werden${COLOR_RESET}"
        fi
    else
        echo -e "${COLOR_WARNING}⚠️  create-desktop-shortcut.sh nicht gefunden${COLOR_RESET}"
    fi
else
    echo -e "${COLOR_INFO}ℹ️  Desktop-Verknüpfung wird nicht erstellt${COLOR_RESET}"
fi

echo ""
echo -e "${COLOR_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
echo -e "${COLOR_BOLD}🚀 Starte update-all.sh mit Modus: $UPDATE_MODE${COLOR_RESET}"
echo -e "${COLOR_BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
echo ""

# Starte update-all.sh mit gewähltem Modus
if [ -n "$UPDATE_MODE" ]; then
    exec bash "$UPDATE_SCRIPT" "$UPDATE_MODE"
else
    exec bash "$UPDATE_SCRIPT"
fi

