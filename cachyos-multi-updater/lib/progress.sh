#!/bin/bash
#
# CachyOS Multi-Updater - Progress Indicator Module
# Module for displaying update progress
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)
#
# This is free and open source software (FOSS).
# You are welcome to modify and distribute it under the terms of the MIT License.
#
# Repository: https://github.com/SunnyCueq/cachyos-multi-updater
#

# ========== Fortschritts-Indikator ==========
show_progress() {
    local step="$1"
    local total="$2"
    local name="$3"
    local status="${4:-⏳}"  # ⏳ wartend, 🔄 läuft, ✅ fertig, ❌ fehler, ⏭️ übersprungen

    local percentage=$((step * 100 / total))
    local bar_length=40
    local filled_length=$((percentage * bar_length / 100))
    local empty_length=$((bar_length - filled_length))

    # Fortschrittsbalken erstellen
    local bar=""
    local i
    for ((i=0; i<filled_length; i++)); do
        bar="${bar}█"
    done
    for ((i=0; i<empty_length; i++)); do
        bar="${bar}░"
    done

    case "$status" in
        "⏳") # Wartend
            echo ""
            echo -e "${COLOR_WARNING}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
            echo -e "${COLOR_WARNING}$status${COLOR_RESET}  ${COLOR_BOLD}$name${COLOR_RESET}"
            echo -e "${COLOR_WARNING}[$bar]${COLOR_RESET} ${COLOR_BOLD}$percentage%${COLOR_RESET} [$step/$total]"
            echo -e "${COLOR_WARNING}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
            echo ""
            ;;
        "🔄") # Läuft
            echo ""
            echo -e "${COLOR_INFO}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
            echo -e "${COLOR_INFO}$status${COLOR_RESET}  ${COLOR_BOLD}$name${COLOR_RESET}"
            echo -e "${COLOR_INFO}[$bar]${COLOR_RESET} ${COLOR_BOLD}$percentage%${COLOR_RESET} [$step/$total]"
            echo -e "${COLOR_INFO}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
            echo ""
            ;;
        "✅") # Fertig
            echo -e "${COLOR_SUCCESS}✅ $name abgeschlossen${COLOR_RESET}"
            echo ""
            ;;
        "❌") # Fehler
            echo ""
            echo -e "${COLOR_ERROR}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
            echo -e "${COLOR_ERROR}❌ FEHLER:${COLOR_RESET} ${COLOR_BOLD}$name${COLOR_RESET}"
            echo -e "${COLOR_ERROR}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
            echo ""
            ;;
        "⏭️") # Übersprungen
            echo -e "${COLOR_WARNING}⏭️  $name übersprungen${COLOR_RESET}"
            echo ""
            ;;
        *)
            echo ""
            echo "[$step/$total] $status $name"
            echo ""
            ;;
    esac
}

calculate_total_steps() {
    local steps=0

    [ "$UPDATE_SYSTEM" = "true" ] && steps=$((steps + 1))
    [ "$UPDATE_AUR" = "true" ] && steps=$((steps + 1))
    [ "$UPDATE_CURSOR" = "true" ] && steps=$((steps + 1))
    [ "$UPDATE_ADGUARD" = "true" ] && steps=$((steps + 1))
    [ "$UPDATE_FLATPAK" = "true" ] && steps=$((steps + 1))

    echo "$steps"
}
