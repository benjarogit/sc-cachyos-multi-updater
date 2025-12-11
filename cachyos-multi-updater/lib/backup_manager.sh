#!/bin/bash
#
# CachyOS Multi-Updater - Backup Management Module
# Manages backups for AdGuard Home and other components
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)

# ========== Find AdGuard Backups ==========
# Finds all AdGuard backup directories
# Returns: space-separated list of backup paths
find_adguard_backups() {
    local backups=""
    
    # Check common backup locations
    local backup_locations=(
        "$HOME/AdGuardHome-backup-*"
        "$HOME/Bilder/AdGuardHome-backup-*"
        "$HOME/Pictures/AdGuardHome-backup-*"
        "$HOME/.config/AdGuardHome/backups/*"
        "$HOME/AdGuardHome/backups/*"
    )
    
    for pattern in "${backup_locations[@]}"; do
        # Use find to handle glob patterns safely
        while IFS= read -r -d '' backup; do
            if [ -d "$backup" ]; then
                backups="${backups} ${backup}"
            fi
        done < <(find "$(dirname "$pattern")" -maxdepth 1 -type d -name "$(basename "$pattern")" -print0 2>/dev/null || true)
    done
    
    # Trim leading space and return
    echo "${backups# }"
}

# ========== Cleanup Old AdGuard Backups ==========
# Removes old AdGuard backups, keeping only the most recent N backups
# Parameters:
#   $1: Number of backups to keep (default: 3)
cleanup_old_adguard_backups() {
    local keep_count="${1:-3}"
    local backups
    backups=$(find_adguard_backups)
    
    if [ -z "$backups" ]; then
        return 0
    fi
    
    # Convert to array and sort by modification time (newest first)
    local backup_array=()
    while IFS= read -r backup; do
        [ -n "$backup" ] && backup_array+=("$backup")
    done <<< "$backups"
    
    # Sort by modification time (newest first)
    local sorted_backups
    sorted_backups=$(printf '%s\n' "${backup_array[@]}" | xargs -I {} sh -c 'echo "$(stat -c %Y "{}" 2>/dev/null || echo 0) {}"' | sort -rn | cut -d' ' -f2-)
    
    # Count total backups
    local total_count
    total_count=$(echo "$sorted_backups" | grep -c . || echo "0")
    
    if [ "$total_count" -le "$keep_count" ]; then
        return 0
    fi
    
    # Remove old backups (skip first $keep_count)
    local removed=0
    local line_num=0
    while IFS= read -r backup; do
        [ -z "$backup" ] && continue
        line_num=$((line_num + 1))
        if [ "$line_num" -gt "$keep_count" ]; then
            log_info "$(t 'log_removing_old_backup') $backup"
            rm -rf "$backup" 2>/dev/null && removed=$((removed + 1)) || log_warning "$(t 'log_backup_removal_failed') $backup"
        fi
    done <<< "$sorted_backups"
    
    if [ "$removed" -gt 0 ]; then
        log_success "$(t 'log_backups_cleaned') $removed $(t 'log_backups_removed')"
    fi
    
    return 0
}

# ========== Create AdGuard Backup ==========
# Creates a backup of AdGuard Home configuration
# Parameters:
#   $1: AdGuard Home directory (default: $HOME/AdGuardHome)
# Returns: backup directory path
create_adguard_backup() {
    local agh_dir="${1:-$HOME/AdGuardHome}"
    local backup_dir="${agh_dir}-backup-$(date +%Y%m%d-%H%M%S)"
    
    if [ ! -d "$agh_dir" ]; then
        log_warning "$(t 'log_adguard_dir_not_found') $agh_dir"
        return 1
    fi
    
    mkdir -p "$backup_dir"
    
    # Backup configuration and data
    if [ -f "$agh_dir/AdGuardHome.yaml" ]; then
        cp "$agh_dir/AdGuardHome.yaml" "$backup_dir/" 2>/dev/null || log_warning "$(t 'log_backup_config_failed')"
    fi
    
    if [ -d "$agh_dir/data" ]; then
        cp -r "$agh_dir/data" "$backup_dir/" 2>/dev/null || log_warning "$(t 'log_backup_data_failed')"
    fi
    
    log_info "$(t 'log_backup_created') $backup_dir"
    echo "$backup_dir"
    return 0
}

