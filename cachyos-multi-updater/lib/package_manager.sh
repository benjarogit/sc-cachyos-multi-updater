#!/bin/bash
#
# CachyOS Multi-Updater - Package Manager Abstraction Module
# Provides abstraction layer for different package managers
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)

# ========== Package Manager Detection ==========
# Detects available package managers
# Returns: space-separated list of available package managers
detect_package_managers() {
    local managers=""
    
    # Check for pacman (Arch-based)
    if command -v pacman >/dev/null 2>&1; then
        managers="${managers} pacman"
    fi
    
    # Check for apt/apt-get (Debian-based)
    if command -v apt >/dev/null 2>&1 || command -v apt-get >/dev/null 2>&1; then
        managers="${managers} apt"
    fi
    
    # Check for dnf/yum (Fedora-based)
    if command -v dnf >/dev/null 2>&1; then
        managers="${managers} dnf"
    elif command -v yum >/dev/null 2>&1; then
        managers="${managers} yum"
    fi
    
    # Check for zypper (openSUSE)
    if command -v zypper >/dev/null 2>&1; then
        managers="${managers} zypper"
    fi
    
    # Check for flatpak (universal)
    if command -v flatpak >/dev/null 2>&1; then
        managers="${managers} flatpak"
    fi
    
    # Check for snap (Ubuntu/Debian)
    if command -v snap >/dev/null 2>&1; then
        managers="${managers} snap"
    fi
    
    # Trim leading space
    echo "${managers# }"
}

# ========== Get Primary Package Manager ==========
# Returns the primary package manager based on distribution
get_primary_package_manager() {
    local distro
    distro=$(detect_distribution)
    
    case "$distro" in
        arch)
            if command -v pacman >/dev/null 2>&1; then
                echo "pacman"
            else
                echo "unknown"
            fi
            ;;
        debian)
            if command -v apt >/dev/null 2>&1; then
                echo "apt"
            elif command -v apt-get >/dev/null 2>&1; then
                echo "apt-get"
            else
                echo "unknown"
            fi
            ;;
        fedora)
            if command -v dnf >/dev/null 2>&1; then
                echo "dnf"
            elif command -v yum >/dev/null 2>&1; then
                echo "yum"
            else
                echo "unknown"
            fi
            ;;
        opensuse)
            if command -v zypper >/dev/null 2>&1; then
                echo "zypper"
            else
                echo "unknown"
            fi
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# ========== Get Package Manager Priority ==========
# Returns package managers in priority order for the distribution
get_package_manager_priority() {
    local distro
    distro=$(detect_distribution)
    
    case "$distro" in
        arch)
            echo "pacman aur flatpak snap"
            ;;
        debian)
            echo "apt flatpak snap"
            ;;
        fedora)
            echo "dnf flatpak"
            ;;
        opensuse)
            echo "zypper flatpak"
            ;;
        *)
            # Fallback: return all available
            detect_package_managers
            ;;
    esac
}

# ========== Check if Package Manager is Available ==========
# Returns 0 if available, 1 if not
is_package_manager_available() {
    local pm="$1"
    
    case "$pm" in
        pacman)
            command -v pacman >/dev/null 2>&1
            ;;
        apt|apt-get)
            command -v apt >/dev/null 2>&1 || command -v apt-get >/dev/null 2>&1
            ;;
        dnf)
            command -v dnf >/dev/null 2>&1
            ;;
        yum)
            command -v yum >/dev/null 2>&1
            ;;
        zypper)
            command -v zypper >/dev/null 2>&1
            ;;
        flatpak)
            command -v flatpak >/dev/null 2>&1
            ;;
        snap)
            command -v snap >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac
}

# ========== Get System Update Command ==========
# Returns the command to update system packages
get_system_update_command() {
    local distro
    distro=$(detect_distribution)
    
    case "$distro" in
        arch)
            echo "pacman -Syu --noconfirm"
            ;;
        debian)
            echo "apt update && apt upgrade -y"
            ;;
        fedora)
            if command -v dnf >/dev/null 2>&1; then
                echo "dnf upgrade -y"
            else
                echo "yum update -y"
            fi
            ;;
        opensuse)
            echo "zypper update -y"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# ========== Get Orphan Removal Command ==========
# Returns the command to remove orphan packages
get_orphan_removal_command() {
    local distro
    distro=$(detect_distribution)
    
    case "$distro" in
        arch)
            echo "pacman -Rns \$(pacman -Qtdq) --noconfirm"
            ;;
        debian)
            echo "apt autoremove -y"
            ;;
        fedora)
            if command -v dnf >/dev/null 2>&1; then
                echo "dnf autoremove -y"
            else
                echo "yum autoremove -y"
            fi
            ;;
        opensuse)
            echo "zypper packages --orphaned | grep -v '^#' | awk '{print \$5}' | xargs -r zypper remove -y"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# ========== Get Cache Cleanup Command ==========
# Returns the command to clean package cache
get_cache_cleanup_command() {
    local distro
    distro=$(detect_distribution)
    
    case "$distro" in
        arch)
            echo "paccache -rk3 && pacman -Sc --noconfirm"
            ;;
        debian)
            echo "apt clean && apt autoclean"
            ;;
        fedora)
            if command -v dnf >/dev/null 2>&1; then
                echo "dnf clean all"
            else
                echo "yum clean all"
            fi
            ;;
        opensuse)
            echo "zypper clean"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# ========== AUR Helper Detection ==========
# Detects available AUR helpers (yay, paru)
# Returns: yay, paru, or unknown
detect_aur_helper() {
    # Check for yay first (preferred)
    if command -v yay >/dev/null 2>&1; then
        echo "yay"
        return
    fi
    
    # Check for paru
    if command -v paru >/dev/null 2>&1; then
        echo "paru"
        return
    fi
    
    echo "unknown"
}

# ========== Check if AUR Helper is Available ==========
# Returns 0 if available, 1 if not
is_aur_helper_available() {
    local helper
    helper=$(detect_aur_helper)
    
    case "$helper" in
        yay|paru)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# ========== Get AUR Update Command ==========
# Returns the command to update AUR packages
get_aur_update_command() {
    local helper
    helper=$(detect_aur_helper)
    
    case "$helper" in
        yay)
            echo "yay -Syu --noconfirm"
            ;;
        paru)
            echo "paru -Syu --noconfirm"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

