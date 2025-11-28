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
    echo -e "${COLOR_BOLD}🎮 INTERAKTIVER MODUS${COLOR_RESET}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Welche Komponenten möchtest du aktualisieren?"
    echo ""

    # System-Updates
    read -p "  [1] System (pacman)?        (J/n): " -n 1 REPLY_SYSTEM
    echo ""
    if [[ ! "$REPLY_SYSTEM" =~ ^[Nn]$ ]]; then
        UPDATE_SYSTEM=true
        echo -e "      ${COLOR_SUCCESS}✅ System-Updates aktiviert${COLOR_RESET}"
    else
        UPDATE_SYSTEM=false
        echo -e "      ${COLOR_WARNING}⏭️  System-Updates übersprungen${COLOR_RESET}"
    fi

    # AUR-Updates
    read -p "  [2] AUR (yay/paru)?         (J/n): " -n 1 REPLY_AUR
    echo ""
    if [[ ! "$REPLY_AUR" =~ ^[Nn]$ ]]; then
        UPDATE_AUR=true
        echo -e "      ${COLOR_SUCCESS}✅ AUR-Updates aktiviert${COLOR_RESET}"
    else
        UPDATE_AUR=false
        echo -e "      ${COLOR_WARNING}⏭️  AUR-Updates übersprungen${COLOR_RESET}"
    fi

    # Cursor
    read -p "  [3] Cursor Editor?          (J/n): " -n 1 REPLY_CURSOR
    echo ""
    if [[ ! "$REPLY_CURSOR" =~ ^[Nn]$ ]]; then
        UPDATE_CURSOR=true
        echo -e "      ${COLOR_SUCCESS}✅ Cursor-Update aktiviert${COLOR_RESET}"
    else
        UPDATE_CURSOR=false
        echo -e "      ${COLOR_WARNING}⏭️  Cursor-Update übersprungen${COLOR_RESET}"
    fi

    # AdGuard Home
    read -p "  [4] AdGuard Home?           (J/n): " -n 1 REPLY_ADGUARD
    echo ""
    if [[ ! "$REPLY_ADGUARD" =~ ^[Nn]$ ]]; then
        UPDATE_ADGUARD=true
        echo -e "      ${COLOR_SUCCESS}✅ AdGuard Home-Update aktiviert${COLOR_RESET}"
    else
        UPDATE_ADGUARD=false
        echo -e "      ${COLOR_WARNING}⏭️  AdGuard Home-Update übersprungen${COLOR_RESET}"
    fi

    # Flatpak
    read -p "  [5] Flatpak?                (J/n): " -n 1 REPLY_FLATPAK
    echo ""
    if [[ ! "$REPLY_FLATPAK" =~ ^[Nn]$ ]]; then
        UPDATE_FLATPAK=true
        echo -e "      ${COLOR_SUCCESS}✅ Flatpak-Updates aktiviert${COLOR_RESET}"
    else
        UPDATE_FLATPAK=false
        echo -e "      ${COLOR_WARNING}⏭️  Flatpak-Updates übersprungen${COLOR_RESET}"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Bestätigung
    echo "Ausgewählte Updates:"
    [ "$UPDATE_SYSTEM" = "true" ] && echo "  ✅ System-Updates"
    [ "$UPDATE_AUR" = "true" ] && echo "  ✅ AUR-Updates"
    [ "$UPDATE_CURSOR" = "true" ] && echo "  ✅ Cursor-Update"
    [ "$UPDATE_ADGUARD" = "true" ] && echo "  ✅ AdGuard Home-Update"
    [ "$UPDATE_FLATPAK" = "true" ] && echo "  ✅ Flatpak-Updates"

    echo ""
    read -p "Fortfahren? (J/n): " -n 1 REPLY_CONTINUE
    echo ""

    if [[ "$REPLY_CONTINUE" =~ ^[Nn]$ ]]; then
        echo "Abgebrochen."
        exit 0
    fi

    echo ""
    log_info "Interaktiver Modus: System=$UPDATE_SYSTEM, AUR=$UPDATE_AUR, Cursor=$UPDATE_CURSOR, AdGuard=$UPDATE_ADGUARD, Flatpak=$UPDATE_FLATPAK"
}
