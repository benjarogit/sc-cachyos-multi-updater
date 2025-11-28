#!/bin/bash
#
# CachyOS Multi-Updater - Summary Module
# Module for displaying compact update summary
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)
#
# This is free and open source software (FOSS).
# You are welcome to modify and distribute it under the terms of the MIT License.
#
# Repository: https://github.com/SunnyCueq/cachyos-multi-updater
#

# ========== Kompakte Update-Zusammenfassung ==========
show_update_summary() {
    local duration="$1"
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${COLOR_BOLD}✅ $(t 'update_completed_title')${COLOR_RESET}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Dauer
    if [ $minutes -gt 0 ]; then
        echo -e "⏱️  $(t 'duration_label') ${COLOR_BOLD}${minutes}m ${seconds}s${COLOR_RESET}"
    else
        echo -e "⏱️  $(t 'duration_label') ${COLOR_BOLD}${seconds}s${COLOR_RESET}"
    fi
    echo ""

    # Aktualisierte Komponenten
    local updated_count=0

    if [ "$UPDATE_SYSTEM" = "true" ] && [ "$SYSTEM_UPDATED" = "true" ]; then
        SYSTEM_PACKAGES_CLEAN=$(echo "$SYSTEM_PACKAGES" | tr -d '\n\r' | grep -oE '[0-9]+' | head -1 || echo "0")
        if [ -n "$SYSTEM_PACKAGES_CLEAN" ] && [ "$SYSTEM_PACKAGES_CLEAN" -gt 0 ] 2>/dev/null; then
            echo -e "${COLOR_SUCCESS}✓${COLOR_RESET} $(t 'system_label') $SYSTEM_PACKAGES_CLEAN $(t 'packages')"
            updated_count=$((updated_count + 1))
        fi
    fi

    if [ "$UPDATE_AUR" = "true" ] && [ "$AUR_UPDATED" = "true" ]; then
        if [ -n "$AUR_PACKAGES" ] && [ "$AUR_PACKAGES" -gt 0 ] 2>/dev/null; then
            echo -e "${COLOR_SUCCESS}✓${COLOR_RESET} $(t 'aur_label') $AUR_PACKAGES $(t 'packages')"
            updated_count=$((updated_count + 1))
        fi
    fi

    if [ "$UPDATE_CURSOR" = "true" ] && [ "$CURSOR_UPDATED" = "true" ]; then
        echo -e "${COLOR_SUCCESS}✓${COLOR_RESET} $(t 'cursor_updated')"
        updated_count=$((updated_count + 1))
    fi

    if [ "$UPDATE_ADGUARD" = "true" ] && [ "$ADGUARD_UPDATED" = "true" ]; then
        echo -e "${COLOR_SUCCESS}✓${COLOR_RESET} $(t 'adguard_updated_label')"
        updated_count=$((updated_count + 1))
    fi

    if [ "$UPDATE_FLATPAK" = "true" ] && [ "$FLATPAK_UPDATED" = "true" ]; then
        FLATPAK_PACKAGES_CLEAN=$(echo "$FLATPAK_PACKAGES" | tr -d '\n\r' | grep -oE '[0-9]+' | head -1 || echo "0")
        if [ -n "$FLATPAK_PACKAGES_CLEAN" ] && [ "$FLATPAK_PACKAGES_CLEAN" -gt 0 ] 2>/dev/null; then
            echo -e "${COLOR_SUCCESS}✓${COLOR_RESET} $(t 'flatpak_updates'): $FLATPAK_PACKAGES_CLEAN $(t 'packages')"
            updated_count=$((updated_count + 1))
        fi
    fi

    # Falls nichts aktualisiert wurde
    if [ $updated_count -eq 0 ]; then
        echo -e "${COLOR_WARNING}○${COLOR_RESET} $(t 'all_components_current')"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# ========== Dry-Run Zusammenfassung ==========
show_dry_run_summary() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${COLOR_WARNING}🔍 $(t 'dry_run_completed')${COLOR_RESET}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${COLOR_WARNING}$(t 'no_changes_made')${COLOR_RESET}"
    echo "$(t 'run_without_dry_run')"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}
