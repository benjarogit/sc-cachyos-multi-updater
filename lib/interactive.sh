#!/bin/bash
#
# CachyOS Multi-Updater - Interactive Mode Module
# Module for interactive component selection
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)
#
# This is free and open source software (FOSS).
# You are welcome to modify and distribute it under the terms of the MIT License.
#
# Repository: https://github.com/SunnyCueq/cachyos-multi-updater
#

# ========== Interaktiver Modus ==========
interactive_mode() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${COLOR_BOLD}🎮 $(t 'interactive_mode')${COLOR_RESET}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "$(t 'which_components_update')"
    echo ""

    # System-Updates
    read -p "  [1] $(t 'system_pacman')        (J/n): " -n 1 REPLY_SYSTEM
    echo ""
    if [[ ! "$REPLY_SYSTEM" =~ ^[Nn]$ ]]; then
        UPDATE_SYSTEM=true
        echo -e "      ${COLOR_SUCCESS}✅ $(t 'system_updates') $(t 'enabled')${COLOR_RESET}"
    else
        UPDATE_SYSTEM=false
        echo -e "      ${COLOR_WARNING}⏭️  $(t 'system_updates') $(t 'skipped')${COLOR_RESET}"
    fi

    # AUR-Updates
    read -p "  [2] $(t 'aur_yay_paru')         (J/n): " -n 1 REPLY_AUR
    echo ""
    if [[ ! "$REPLY_AUR" =~ ^[Nn]$ ]]; then
        UPDATE_AUR=true
        echo -e "      ${COLOR_SUCCESS}✅ $(t 'aur_updates') $(t 'enabled')${COLOR_RESET}"
    else
        UPDATE_AUR=false
        echo -e "      ${COLOR_WARNING}⏭️  $(t 'aur_updates') $(t 'skipped')${COLOR_RESET}"
    fi

    # Cursor
    read -p "  [3] $(t 'cursor_editor')          (J/n): " -n 1 REPLY_CURSOR
    echo ""
    if [[ ! "$REPLY_CURSOR" =~ ^[Nn]$ ]]; then
        UPDATE_CURSOR=true
        echo -e "      ${COLOR_SUCCESS}✅ $(t 'cursor_editor_update') $(t 'enabled')${COLOR_RESET}"
    else
        UPDATE_CURSOR=false
        echo -e "      ${COLOR_WARNING}⏭️  $(t 'cursor_editor_update') $(t 'skipped')${COLOR_RESET}"
    fi

    # AdGuard Home
    read -p "  [4] $(t 'adguard_home')           (J/n): " -n 1 REPLY_ADGUARD
    echo ""
    if [[ ! "$REPLY_ADGUARD" =~ ^[Nn]$ ]]; then
        UPDATE_ADGUARD=true
        echo -e "      ${COLOR_SUCCESS}✅ $(t 'adguard_home_update') $(t 'enabled')${COLOR_RESET}"
    else
        UPDATE_ADGUARD=false
        echo -e "      ${COLOR_WARNING}⏭️  $(t 'adguard_home_update') $(t 'skipped')${COLOR_RESET}"
    fi

    # Flatpak
    read -p "  [5] $(t 'flatpak')                (J/n): " -n 1 REPLY_FLATPAK
    echo ""
    if [[ ! "$REPLY_FLATPAK" =~ ^[Nn]$ ]]; then
        UPDATE_FLATPAK=true
        echo -e "      ${COLOR_SUCCESS}✅ $(t 'flatpak_updates') $(t 'enabled')${COLOR_RESET}"
    else
        UPDATE_FLATPAK=false
        echo -e "      ${COLOR_WARNING}⏭️  $(t 'flatpak_updates') $(t 'skipped')${COLOR_RESET}"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Bestätigung
    echo "$(t 'selected_updates')"
    [ "$UPDATE_SYSTEM" = "true" ] && echo "  ✅ $(t 'system_updates')"
    [ "$UPDATE_AUR" = "true" ] && echo "  ✅ $(t 'aur_updates')"
    [ "$UPDATE_CURSOR" = "true" ] && echo "  ✅ $(t 'cursor_editor_update')"
    [ "$UPDATE_ADGUARD" = "true" ] && echo "  ✅ $(t 'adguard_home_update')"
    [ "$UPDATE_FLATPAK" = "true" ] && echo "  ✅ $(t 'flatpak_updates')"

    echo ""
    read -p "$(t 'continue_question') " -n 1 REPLY_CONTINUE
    echo ""

    if [[ "$REPLY_CONTINUE" =~ ^[Nn]$ ]]; then
        echo "$(t 'cancelled')"
        exit 0
    fi

    echo ""
    log_info "Interaktiver Modus: System=$UPDATE_SYSTEM, AUR=$UPDATE_AUR, Cursor=$UPDATE_CURSOR, AdGuard=$UPDATE_ADGUARD, Flatpak=$UPDATE_FLATPAK"
}
