#!/bin/bash
#
# CachyOS Multi-Updater - Enhanced Cleanup Module
# Provides multi-distribution cleanup functions
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)

# ========== Remove Orphan Packages ==========
# Removes orphan packages based on distribution
remove_orphan_packages() {
    local distro
    distro=$(detect_distribution)
    
    case "$distro" in
        arch)
            local orphans
            orphans=$(pacman -Qtdq 2>/dev/null || true)
            if [ -n "$orphans" ]; then
                log_info "$(t 'log_removing_orphans')"
                sudo pacman -Rns $orphans --noconfirm 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_orphans_removal_failed')"
            else
                log_info "$(t 'log_no_orphans')"
            fi
            ;;
        debian)
            log_info "$(t 'log_removing_orphans')"
            sudo apt autoremove -y 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_orphans_removal_failed')"
            ;;
        fedora)
            if command -v dnf >/dev/null 2>&1; then
                log_info "$(t 'log_removing_orphans')"
                sudo dnf autoremove -y 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_orphans_removal_failed')"
            else
                log_info "$(t 'log_removing_orphans')"
                sudo yum autoremove -y 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_orphans_removal_failed')"
            fi
            ;;
        opensuse)
            log_info "$(t 'log_removing_orphans')"
            local orphans
            orphans=$(zypper packages --orphaned 2>/dev/null | grep -v '^#' | awk '{print $5}' | grep -v '^$' || true)
            if [ -n "$orphans" ]; then
                echo "$orphans" | xargs -r sudo zypper remove -y 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_orphans_removal_failed')"
            else
                log_info "$(t 'log_no_orphans')"
            fi
            ;;
        *)
            log_warning "$(t 'log_orphans_not_supported') $distro"
            ;;
    esac
}

# ========== Clean Package Cache ==========
# Cleans package cache based on distribution
clean_package_cache() {
    local distro
    distro=$(detect_distribution)
    
    case "$distro" in
        arch)
            log_info "$(t 'log_cleaning_package_cache')"
            paccache -rk3 2>&1 | tee -a "$LOG_FILE" || log_warning "Paccache fehlgeschlagen"
            log_info "$(t 'log_removing_old_packages')"
            yes | sudo pacman -Sc --noconfirm 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_package_cache_warnings')"
            ;;
        debian)
            log_info "$(t 'log_cleaning_package_cache')"
            sudo apt clean 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_package_cache_warnings')"
            sudo apt autoclean 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_package_cache_warnings')"
            ;;
        fedora)
            log_info "$(t 'log_cleaning_package_cache')"
            if command -v dnf >/dev/null 2>&1; then
                sudo dnf clean all 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_package_cache_warnings')"
            else
                sudo yum clean all 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_package_cache_warnings')"
            fi
            ;;
        opensuse)
            log_info "$(t 'log_cleaning_package_cache')"
            sudo zypper clean 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_package_cache_warnings')"
            ;;
        *)
            log_warning "$(t 'log_cache_cleanup_not_supported') $distro"
            ;;
    esac
}

# ========== Clean Temporary Files ==========
# Removes temporary files from /tmp
clean_temporary_files() {
    log_info "$(t 'log_cleaning_temp_files')"
    
    # Cursor temporäre Dateien
    if find /tmp -maxdepth 1 -name "*cursor*" -type d 2>/dev/null | grep -q .; then
        log_info "$(t 'log_removing_cursor_temp')"
        find /tmp -maxdepth 1 -name "*cursor*" -type d -exec rm -rf {} + 2>/dev/null || true
        log_success "$(t 'log_cursor_temp_removed')"
    fi
    
    # AdGuard temporäre Dateien
    if find /tmp -maxdepth 1 \( -name "*adguard*" -o -name "*AdGuard*" \) -type d 2>/dev/null | grep -q .; then
        log_info "$(t 'log_removing_adguard_temp')"
        find /tmp -maxdepth 1 \( -name "*adguard*" -o -name "*AdGuard*" \) -type d -exec rm -rf {} + 2>/dev/null || true
        log_success "$(t 'log_adguard_temp_removed')"
    fi
    
    # Cursor .deb Dateien im Script-Verzeichnis
    if find "$SCRIPT_DIR" -maxdepth 1 -name "cursor*.deb" -type f 2>/dev/null | grep -q .; then
        log_info "$(t 'log_removing_cursor_deb')"
        find "$SCRIPT_DIR" -maxdepth 1 -name "cursor*.deb" -type f -delete 2>/dev/null || true
        log_success "$(t 'log_cursor_deb_removed')"
    fi
}

# ========== Clean Old Log Files ==========
# Removes old log files (configurable)
clean_old_log_files() {
    local max_log_files="${MAX_LOG_FILES:-3}"
    local log_dir="${LOG_DIR:-$SCRIPT_DIR/logs/update}"
    
    if [ ! -d "$log_dir" ]; then
        return 0
    fi
    
    log_info "$(t 'log_cleaning_old_logs')"
    
    # Sortiere Log-Dateien nach Änderungsdatum (neueste zuerst) und entferne alte
    local log_count
    log_count=$(find "$log_dir" -maxdepth 1 -name "update-*.log" -type f | wc -l)
    
    if [ "$log_count" -gt "$max_log_files" ]; then
        local to_remove
        to_remove=$((log_count - max_log_files))
        find "$log_dir" -maxdepth 1 -name "update-*.log" -type f -printf '%T@ %p\n' | sort -rn | tail -n +$((max_log_files + 1)) | cut -d' ' -f2- | head -n "$to_remove" | xargs -r rm -f 2>/dev/null || true
        log_success "$(t 'log_old_logs_removed') $to_remove"
    else
        log_info "$(t 'log_no_old_logs')"
    fi
}

# ========== Clean Flatpak Cache ==========
# Cleans Flatpak unused runtimes and applications
clean_flatpak_cache() {
    if ! command -v flatpak >/dev/null 2>&1; then
        return 0
    fi
    
    log_info "$(t 'log_cleaning_flatpak_cache')"
    if flatpak uninstall --unused --noninteractive -y 2>&1 | tee -a "$LOG_FILE"; then
        log_success "$(t 'log_flatpak_cache_cleaned')"
    else
        log_warning "$(t 'log_flatpak_cache_warnings')"
    fi
}

# ========== Perform Full Cleanup ==========
# Performs all cleanup operations based on configuration
perform_cleanup() {
    local cleanup_aggressiveness="${CLEANUP_AGGRESSIVENESS:-moderate}"
    local cleanup_orphans="${CLEANUP_ORPHANS:-true}"
    local cleanup_cache="${CLEANUP_CACHE:-true}"
    local cleanup_temp="${CLEANUP_TEMP_FILES:-true}"
    local cleanup_backups="${CLEANUP_OLD_BACKUPS:-true}"
    
    log_info "$(t 'log_starting_cleanup')"
    show_cleanup_start
    
    # Orphan packages
    if [ "$cleanup_orphans" = "true" ]; then
        remove_orphan_packages
    fi
    
    # Package cache
    if [ "$cleanup_cache" = "true" ]; then
        clean_package_cache
    fi
    
    # Temporary files
    if [ "$cleanup_temp" = "true" ]; then
        clean_temporary_files
    fi
    
    # Old backups (AdGuard)
    if [ "$cleanup_backups" = "true" ] && [ -n "${ADGUARD_BACKUP_KEEP_COUNT:-}" ]; then
        cleanup_old_adguard_backups "${ADGUARD_BACKUP_KEEP_COUNT}"
    fi
    
    # Old log files (only in moderate/aggressive mode)
    if [ "$cleanup_aggressiveness" != "safe" ]; then
        clean_old_log_files
    fi
    
    # Flatpak cache
    clean_flatpak_cache
    
    show_cleanup_result
}

