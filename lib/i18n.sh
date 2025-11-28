#!/bin/bash
#
# CachyOS Multi-Updater - Internationalization Module
# Automatic language detection and translation support
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)
#
# This is free and open source software (FOSS).
# You are welcome to modify and distribute it under the terms of the MIT License.
#
# Repository: https://github.com/SunnyCueq/cachyos-multi-updater
#

# ========== Language Detection ==========
detect_language() {
    # Prüfe LANG und LC_ALL Umgebungsvariablen
    local lang="${LANG:-${LC_ALL:-en_US.UTF-8}}"

    # Extrahiere Sprachcode (z.B. de aus de_DE.UTF-8)
    lang="${lang%%_*}"
    lang="${lang%%.*}"

    case "$lang" in
        de|DE)
            echo "de"
            ;;
        *)
            echo "en"
            ;;
    esac
}

# Automatische Spracherkennung
DETECTED_LANG=$(detect_language)

# ========== Load Language File ==========
# Lade die entsprechende Sprachdatei
# Verwende SCRIPT_DIR wenn bereits gesetzt (vom Hauptscript), sonst berechne es
if [ -z "${SCRIPT_DIR:-}" ]; then
    I18N_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    LANG_DIR="$(cd "$I18N_SCRIPT_DIR/../lang" && pwd)"
else
    LANG_DIR="$SCRIPT_DIR/lang"
fi
LANG_FILE="$LANG_DIR/$DETECTED_LANG.sh"

if [ ! -f "$LANG_FILE" ]; then
    # Fallback auf Englisch wenn Sprachdatei nicht gefunden
    LANG_FILE="$LANG_DIR/en.sh"
    if [ ! -f "$LANG_FILE" ]; then
        echo "Error: Language file not found: $LANG_FILE" >&2
        exit 1
    fi
fi

# Lade Sprachdatei
source "$LANG_FILE"

# ========== Translation Function ==========
# Verwendung: t "key"
t() {
    local key="$1"
    
    # Verwende das entsprechende Array basierend auf der erkannten Sprache
    case "$DETECTED_LANG" in
        de)
            if [ -n "${TRANSLATIONS_DE[$key]}" ]; then
                echo "${TRANSLATIONS_DE[$key]}"
            else
                # Fallback: Zeige Key wenn Übersetzung fehlt
                echo "$key"
            fi
            ;;
        *)
            # English (default)
            if [ -n "${TRANSLATIONS_EN[$key]}" ]; then
                echo "${TRANSLATIONS_EN[$key]}"
            else
                # Fallback: Zeige Key wenn Übersetzung fehlt
                echo "$key"
            fi
            ;;
    esac
}
