#!/bin/bash
#
# CachyOS Multi-Updater - Output Module
# Module for clean, structured output during updates
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)
#
# This is free and open source software (FOSS).
# You are welcome to modify and distribute it under the terms of the MIT License.
#
# Repository: https://github.com/SunnyCueq/cachyos-multi-updater
#

# ========== Kompakte Update-Ausgaben ==========

# Zeigt kompakte System-Update-Info
show_system_update_start() {
    echo ""
    echo -e "${COLOR_INFO}▸ $(t 'system_update') $(t 'running')${COLOR_RESET}"
}

show_system_update_result() {
    local count="$1"
    # Bereinige count von Zeilenumbrüchen und Whitespace
    count=$(echo "$count" | tr -d '\n\r' | xargs)
    
    local pkg_word
    if [ "$count" -eq 1 ] 2>/dev/null; then
        pkg_word=$(t 'package')
    else
        pkg_word=$(t 'packages')
    fi
    
    if [ "$count" -gt 0 ] 2>/dev/null; then
        echo -e "${COLOR_SUCCESS}  ✓ $count $pkg_word $(t 'packages_updated')${COLOR_RESET}"
    else
        echo -e "${COLOR_SUCCESS}  ✓ $(t 'already_uptodate')${COLOR_RESET}"
    fi
    echo ""
}

# Zeigt kompakte AUR-Update-Info
show_aur_update_start() {
    echo ""
    echo -e "${COLOR_INFO}▸ $(t 'aur_update') $(t 'running')${COLOR_RESET}"
}

show_aur_update_result() {
    local count="$1"
    # Bereinige count von Zeilenumbrüchen und Whitespace
    count=$(echo "$count" | tr -d '\n\r' | xargs)
    
    local pkg_word
    if [ "$count" -eq 1 ] 2>/dev/null; then
        pkg_word=$(t 'package')
    else
        pkg_word=$(t 'packages')
    fi
    
    if [ "$count" -gt 0 ] 2>/dev/null; then
        echo -e "${COLOR_SUCCESS}  ✓ $count $pkg_word $(t 'packages_updated')${COLOR_RESET}"
    else
        echo -e "${COLOR_SUCCESS}  ✓ $(t 'already_uptodate')${COLOR_RESET}"
    fi
    echo ""
}

# Zeigt kompakte Cursor-Update-Info
show_cursor_update_start() {
    echo ""
    echo -e "${COLOR_INFO}▸ Cursor $(t 'checking')${COLOR_RESET}"
}

show_cursor_update_downloading() {
    local version="$1"
    echo -e "${COLOR_INFO}  ⬇ $(t 'downloading') v$version...${COLOR_RESET}"
}

show_cursor_update_installing() {
    echo -e "${COLOR_INFO}  📦 $(t 'installing')${COLOR_RESET}"
}

show_cursor_update_result() {
    local old_version="$1"
    local new_version="$2"
    if [ "$old_version" != "$new_version" ]; then
        echo -e "${COLOR_SUCCESS}  ✓ $(t 'updated'): $old_version → $new_version${COLOR_RESET}"
    else
        echo -e "${COLOR_SUCCESS}  ✓ $(t 'already_uptodate') (v$old_version)${COLOR_RESET}"
    fi
    echo ""
}

show_cursor_pacman_managed() {
    local version="$1"
    echo -e "${COLOR_WARNING}  ○ $(t 'managed_by_pacman') (v$version)${COLOR_RESET}"
    echo ""
}

# Zeigt kompakte AdGuard-Update-Info
show_adguard_update_start() {
    echo ""
    echo -e "${COLOR_INFO}▸ AdGuard Home $(t 'checking')${COLOR_RESET}"
}

show_adguard_update_downloading() {
    local version="$1"
    echo -e "${COLOR_INFO}  ⬇ $(t 'downloading') v$version...${COLOR_RESET}"
}

show_adguard_update_result() {
    local old_version="$1"
    local new_version="$2"
    if [ "$old_version" != "$new_version" ]; then
        echo -e "${COLOR_SUCCESS}  ✓ $(t 'updated'): v$old_version → v$new_version${COLOR_RESET}"
    else
        echo -e "${COLOR_SUCCESS}  ✓ $(t 'already_uptodate') (v$old_version)${COLOR_RESET}"
    fi
    echo ""
}

# Zeigt kompakte Flatpak-Update-Info
show_flatpak_update_start() {
    echo ""
    echo -e "${COLOR_INFO}▸ Flatpak $(t 'running')${COLOR_RESET}"
}

show_flatpak_update_result() {
    local count="$1"
    # Bereinige count von Zeilenumbrüchen und Whitespace
    count=$(echo "$count" | tr -d '\n\r' | xargs)
    
    local pkg_word
    if [ "$count" -eq 1 ] 2>/dev/null; then
        pkg_word=$(t 'package')
    else
        pkg_word=$(t 'packages')
    fi
    
    if [ "$count" -gt 0 ] 2>/dev/null; then
        echo -e "${COLOR_SUCCESS}  ✓ $count $pkg_word $(t 'packages_updated')${COLOR_RESET}"
    else
        echo -e "${COLOR_SUCCESS}  ✓ $(t 'already_uptodate')${COLOR_RESET}"
    fi
    echo ""
}

# Zeigt kompakte Cleanup-Info
show_cleanup_start() {
    echo ""
    echo -e "${COLOR_INFO}🧹 $(t 'cleanup')${COLOR_RESET}"
}

show_cleanup_result() {
    echo -e "${COLOR_SUCCESS}  ✓ $(t 'system_cleaned')${COLOR_RESET}"
    echo ""
}

# Zeigt nicht gefundene Komponente
show_component_not_found() {
    local name="$1"
    echo -e "${COLOR_WARNING}  ⊘ $name $(t 'not_installed')${COLOR_RESET}"
    echo ""
}

# Zeigt übersprungene Komponente
show_component_skipped() {
    local name="$1"
    echo -e "${COLOR_WARNING}  ⏭ $name $(t 'skipped')${COLOR_RESET}"
    echo ""
}
