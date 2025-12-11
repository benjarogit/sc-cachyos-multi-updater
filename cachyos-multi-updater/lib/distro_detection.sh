#!/bin/bash
#
# CachyOS Multi-Updater - Distribution Detection Module
# Detects Linux distribution and provides distribution-specific information
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)

# ========== Distribution Detection ==========
# Detects the Linux distribution using multiple methods
# Returns: distribution name (arch, debian, fedora, opensuse, unknown)
detect_distribution() {
    local distro="unknown"
    local id=""
    local id_like=""
    local pretty_name=""
    
    # Method 1: /etc/os-release (most reliable)
    if [ -f /etc/os-release ]; then
        id=$(grep "^ID=" /etc/os-release | cut -d'=' -f2 | tr -d '"' | tr '[:upper:]' '[:lower:]' || echo "")
        id_like=$(grep "^ID_LIKE=" /etc/os-release | cut -d'=' -f2 | tr -d '"' | tr '[:upper:]' '[:lower:]' || echo "")
        pretty_name=$(grep "^PRETTY_NAME=" /etc/os-release | cut -d'=' -f2 | tr -d '"' || echo "")
        
        # Arch-based distributions
        case "$id" in
            arch|archlinux|cachyos|manjaro|endeavouros|arcolinux|artix|garuda|rebornos|parabola)
                distro="arch"
                ;;
        esac
        
        # Check ID_LIKE for Arch-based
        if [ "$distro" = "unknown" ]; then
            case "$id_like" in
                *arch*)
                    distro="arch"
                    ;;
            esac
        fi
        
        # Debian-based distributions
        if [ "$distro" = "unknown" ]; then
            case "$id" in
                debian|ubuntu|linuxmint|mint|elementary|pop|kali|raspbian)
                    distro="debian"
                    ;;
            esac
        fi
        
        # Check ID_LIKE for Debian-based
        if [ "$distro" = "unknown" ]; then
            case "$id_like" in
                *debian*)
                    distro="debian"
                    ;;
            esac
        fi
        
        # Fedora-based distributions
        if [ "$distro" = "unknown" ]; then
            case "$id" in
                fedora|rhel|centos|rocky|almalinux|ol|oracle)
                    distro="fedora"
                    ;;
            esac
        fi
        
        # Check ID_LIKE for Fedora-based
        if [ "$distro" = "unknown" ]; then
            case "$id_like" in
                *fedora*|*rhel*)
                    distro="fedora"
                    ;;
            esac
        fi
        
        # openSUSE
        if [ "$distro" = "unknown" ]; then
            case "$id" in
                opensuse*|sles|sled)
                    distro="opensuse"
                    ;;
            esac
        fi
    fi
    
    # Method 2: lsb_release (fallback)
    if [ "$distro" = "unknown" ] && command -v lsb_release >/dev/null 2>&1; then
        local lsb_id
        lsb_id=$(lsb_release -si 2>/dev/null | tr '[:upper:]' '[:lower:]' || echo "")
        
        case "$lsb_id" in
            *arch*|*manjaro*|*endeavour*|*cachyos*)
                distro="arch"
                ;;
            *debian*|*ubuntu*|*mint*)
                distro="debian"
                ;;
            *fedora*|*redhat*|*centos*)
                distro="fedora"
                ;;
            *suse*|*opensuse*)
                distro="opensuse"
                ;;
        esac
    fi
    
    # Method 3: Package manager detection (last resort)
    if [ "$distro" = "unknown" ]; then
        if command -v pacman >/dev/null 2>&1; then
            distro="arch"
        elif command -v apt >/dev/null 2>&1 || command -v apt-get >/dev/null 2>&1; then
            distro="debian"
        elif command -v dnf >/dev/null 2>&1 || command -v yum >/dev/null 2>&1; then
            distro="fedora"
        elif command -v zypper >/dev/null 2>&1; then
            distro="opensuse"
        fi
    fi
    
    echo "$distro"
}

# ========== Get Distribution Name ==========
# Returns human-readable distribution name
get_distribution_name() {
    local distro
    distro=$(detect_distribution)
    
    case "$distro" in
        arch)
            if [ -f /etc/os-release ]; then
                local pretty_name
                pretty_name=$(grep "^PRETTY_NAME=" /etc/os-release | cut -d'=' -f2 | tr -d '"' || echo "")
                if [ -n "$pretty_name" ]; then
                    echo "$pretty_name"
                    return
                fi
            fi
            echo "Arch Linux"
            ;;
        debian)
            if [ -f /etc/os-release ]; then
                local pretty_name
                pretty_name=$(grep "^PRETTY_NAME=" /etc/os-release | cut -d'=' -f2 | tr -d '"' || echo "")
                if [ -n "$pretty_name" ]; then
                    echo "$pretty_name"
                    return
                fi
            fi
            echo "Debian"
            ;;
        fedora)
            if [ -f /etc/os-release ]; then
                local pretty_name
                pretty_name=$(grep "^PRETTY_NAME=" /etc/os-release | cut -d'=' -f2 | tr -d '"' || echo "")
                if [ -n "$pretty_name" ]; then
                    echo "$pretty_name"
                    return
                fi
            fi
            echo "Fedora"
            ;;
        opensuse)
            if [ -f /etc/os-release ]; then
                local pretty_name
                pretty_name=$(grep "^PRETTY_NAME=" /etc/os-release | cut -d'=' -f2 | tr -d '"' || echo "")
                if [ -n "$pretty_name" ]; then
                    echo "$pretty_name"
                    return
                fi
            fi
            echo "openSUSE"
            ;;
        *)
            echo "Unknown Linux Distribution"
            ;;
    esac
}

# ========== Check if Distribution is Supported ==========
# Returns 0 if supported, 1 if not
is_distribution_supported() {
    local distro
    distro=$(detect_distribution)
    
    case "$distro" in
        arch|debian|fedora|opensuse)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# ========== Get Distribution Family ==========
# Returns: arch, debian, fedora, opensuse, unknown
get_distribution_family() {
    detect_distribution
}

