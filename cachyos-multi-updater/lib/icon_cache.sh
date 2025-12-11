#!/bin/bash
#
# CachyOS Multi-Updater - Icon Cache Update Module
# Updates icon caches based on detected desktop environment
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)

# ========== Detect Desktop Environment ==========
# Detects the desktop environment using multiple methods
# Returns: kde, gnome, xfce, lxde, mate, cinnamon, unknown
detect_desktop_environment() {
    local de="unknown"
    
    # Method 1: XDG_CURRENT_DESKTOP (most reliable)
    if [ -n "${XDG_CURRENT_DESKTOP:-}" ]; then
        local xdg_de
        xdg_de=$(echo "$XDG_CURRENT_DESKTOP" | tr '[:upper:]' '[:lower:]' | cut -d':' -f1)
        case "$xdg_de" in
            *kde*)
                de="kde"
                ;;
            *gnome*)
                de="gnome"
                ;;
            *xfce*)
                de="xfce"
                ;;
            *lxde*)
                de="lxde"
                ;;
            *mate*)
                de="mate"
                ;;
            *cinnamon*)
                de="cinnamon"
                ;;
        esac
    fi
    
    # Method 2: DESKTOP_SESSION (fallback)
    if [ "$de" = "unknown" ] && [ -n "${DESKTOP_SESSION:-}" ]; then
        local session
        session=$(echo "$DESKTOP_SESSION" | tr '[:upper:]' '[:lower:]')
        case "$session" in
            *kde*|*plasma*)
                de="kde"
                ;;
            *gnome*)
                de="gnome"
                ;;
            *xfce*)
                de="xfce"
                ;;
            *lxde*)
                de="lxde"
                ;;
            *mate*)
                de="mate"
                ;;
            *cinnamon*)
                de="cinnamon"
                ;;
        esac
    fi
    
    # Method 3: Running processes (fallback 2)
    if [ "$de" = "unknown" ]; then
        if pgrep -x kwin >/dev/null 2>&1 || pgrep -x plasmashell >/dev/null 2>&1; then
            de="kde"
        elif pgrep -x gnome-shell >/dev/null 2>&1; then
            de="gnome"
        elif pgrep -x xfce4-session >/dev/null 2>&1; then
            de="xfce"
        elif pgrep -x lxsession >/dev/null 2>&1; then
            de="lxde"
        elif pgrep -x mate-session >/dev/null 2>&1; then
            de="mate"
        elif pgrep -x cinnamon-session >/dev/null 2>&1; then
            de="cinnamon"
        fi
    fi
    
    # Method 4: Config files (fallback 3)
    if [ "$de" = "unknown" ]; then
        if [ -d "$HOME/.config/kde" ] || [ -d "$HOME/.kde" ]; then
            de="kde"
        elif [ -d "$HOME/.config/gnome" ]; then
            de="gnome"
        elif [ -d "$HOME/.config/xfce4" ]; then
            de="xfce"
        fi
    fi
    
    echo "$de"
}

# ========== Update Icon Cache ==========
# Updates icon cache based on desktop environment
update_icon_cache() {
    local de
    de=$(detect_desktop_environment)
    local icon_cache_timing="${ICON_CACHE_UPDATE:-both}"
    
    log_info "$(t 'log_desktop_env_detected') $de"
    
    # GTK Icon Cache (for GTK-based DEs)
    if [ "$de" != "kde" ] || [ "$de" = "unknown" ]; then
        if command -v gtk-update-icon-cache >/dev/null 2>&1; then
            log_info "$(t 'log_updating_gtk_icon_cache')"
            gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
            if [ -d "/usr/share/icons/hicolor" ]; then
                sudo gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
            fi
        fi
    fi
    
    # KDE Icon Cache
    if [ "$de" = "kde" ]; then
        if command -v kbuildsycoca6 >/dev/null 2>&1; then
            log_info "$(t 'log_updating_kde_icon_cache')"
            kbuildsycoca6 --noincremental 2>/dev/null || true
        elif command -v kbuildsycoca5 >/dev/null 2>&1; then
            log_info "$(t 'log_updating_kde_icon_cache')"
            kbuildsycoca5 --noincremental 2>/dev/null || true
        fi
    fi
    
    # Desktop Database (universal)
    if command -v update-desktop-database >/dev/null 2>&1; then
        log_info "$(t 'log_updating_desktop_database')"
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
        if [ -d "/usr/share/applications" ]; then
            sudo update-desktop-database /usr/share/applications 2>/dev/null || true
        fi
    fi
    
    log_success "$(t 'log_icon_cache_updated')"
}

