#!/bin/bash
#
# CachyOS Multi-Updater
# Automated update tool for CachyOS, AUR packages, Cursor editor, and AdGuard Home
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)
#
# This is free and open source software (FOSS).
# You are welcome to modify and distribute it under the terms of the MIT License.
#
# Repository: https://github.com/SunnyCueq/cachyos-multi-updater
#

set -euo pipefail

# ========== Version ==========
readonly SCRIPT_VERSION="1.0.5"
readonly GITHUB_REPO="SunnyCueq/cachyos-multi-updater"

# ========== Exit-Codes ==========
# EXIT_SUCCESS=0 wird implizit verwendet (exit 0)
# EXIT_LOCK_EXISTS=1 wird implizit verwendet (exit 1)
# EXIT_CONFIG_ERROR=2 wird implizit verwendet (exit 2)
readonly EXIT_DOWNLOAD_ERROR=3
readonly EXIT_UPDATE_ERROR=4

# ========== Konfiguration ==========
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
LOG_DIR="$SCRIPT_DIR/logs"
readonly LOG_DIR
LOG_FILE="$LOG_DIR/update-$(date +%Y%m%d-%H%M%S).log"
readonly LOG_FILE
MAX_LOG_FILES=3
readonly CONFIG_FILE="$SCRIPT_DIR/config.conf"

# Default-Werte
UPDATE_SYSTEM=true
UPDATE_AUR=true
UPDATE_CURSOR=true
UPDATE_ADGUARD=true
UPDATE_FLATPAK=true
DRY_RUN=false
ENABLE_NOTIFICATIONS=true
ENABLE_COLORS=true
DOWNLOAD_RETRIES=3
ENABLE_AUTO_UPDATE=false

# Tracking-Variablen für Zusammenfassung
START_TIME=$(date +%s)
SYSTEM_UPDATED=false
AUR_UPDATED=false
CURSOR_UPDATED=false
ADGUARD_UPDATED=false
FLATPAK_UPDATED=false
SYSTEM_PACKAGES=0
AUR_PACKAGES=0
FLATPAK_PACKAGES=0

# Statistiken-Verzeichnis
readonly STATS_DIR="$SCRIPT_DIR/.stats"
readonly STATS_FILE="$STATS_DIR/stats.json"
mkdir -p "$STATS_DIR"

# Log-Verzeichnis erstellen
mkdir -p "$LOG_DIR"

# ========== Config-Validierung ==========
validate_config_value() {
    local key="$1"
    local value="$2"

    case "$key" in
        DRY_RUN|ENABLE_NOTIFICATIONS|ENABLE_COLORS|ENABLE_AUTO_UPDATE)
            if [[ ! "$value" =~ ^(true|false)$ ]]; then
                echo "$(t 'config_invalid_value') $key: '$value' $(t 'config_expected') true/false)" >&2
                return 1
            fi
            ;;
        MAX_LOG_FILES|DOWNLOAD_RETRIES)
            if [[ ! "$value" =~ ^[0-9]+$ ]]; then
                echo "$(t 'config_invalid_value') $key: '$value' $(t 'config_expected') number)" >&2
                return 1
            fi
            ;;
    esac
    return 0
}

# ========== Konfigurationsdatei laden ==========
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        local line_num=0
        # Source config file (sicher laden)
        while IFS='=' read -r key value || [ -n "$key" ]; do
            ((line_num++))
            # Ignoriere Kommentare und leere Zeilen
            [[ "$key" =~ ^[[:space:]]*# ]] && continue
            [[ -z "$key" ]] && continue

            # Entferne führende/trailing Whitespace
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs)

            # Validiere Wert
            if ! validate_config_value "$key" "$value"; then
                echo "  $(t 'config_in_line') $line_num $(t 'config_of') $CONFIG_FILE" >&2
                continue
            fi

            # Setze Variablen
            case "$key" in
                ENABLE_SYSTEM_UPDATE) UPDATE_SYSTEM=$(echo "$value" | tr '[:upper:]' '[:lower:]') ;;
                ENABLE_AUR_UPDATE) UPDATE_AUR=$(echo "$value" | tr '[:upper:]' '[:lower:]') ;;
                ENABLE_CURSOR_UPDATE) UPDATE_CURSOR=$(echo "$value" | tr '[:upper:]' '[:lower:]') ;;
                ENABLE_ADGUARD_UPDATE) UPDATE_ADGUARD=$(echo "$value" | tr '[:upper:]' '[:lower:]') ;;
                ENABLE_FLATPAK_UPDATE) UPDATE_FLATPAK=$(echo "$value" | tr '[:upper:]' '[:lower:]') ;;
                DRY_RUN) DRY_RUN=$(echo "$value" | tr '[:upper:]' '[:lower:]') ;;
                ENABLE_NOTIFICATIONS) ENABLE_NOTIFICATIONS=$(echo "$value" | tr '[:upper:]' '[:lower:]') ;;
                MAX_LOG_FILES) MAX_LOG_FILES="$value" ;;
                ENABLE_COLORS) ENABLE_COLORS=$(echo "$value" | tr '[:upper:]' '[:lower:]') ;;
                DOWNLOAD_RETRIES) DOWNLOAD_RETRIES="$value" ;;
                ENABLE_AUTO_UPDATE) ENABLE_AUTO_UPDATE=$(echo "$value" | tr '[:upper:]' '[:lower:]') ;;
            esac
        done < "$CONFIG_FILE" || true
    fi
}

load_config

# ========== Farben (MUSS vor Logging-Funktionen gesetzt werden!) ==========
if [ "$ENABLE_COLORS" = "true" ] && [ -t 1 ]; then
    readonly COLOR_RESET='\033[0m'
    readonly COLOR_INFO='\033[0;36m'      # Cyan
    readonly COLOR_SUCCESS='\033[0;32m'   # Green
    readonly COLOR_ERROR='\033[0;31m'     # Red
    readonly COLOR_WARNING='\033[0;33m'   # Yellow
    readonly COLOR_BOLD='\033[1m'         # Bold
else
    readonly COLOR_RESET=''
    readonly COLOR_INFO=''
    readonly COLOR_SUCCESS=''
    readonly COLOR_ERROR=''
    readonly COLOR_WARNING=''
    readonly COLOR_BOLD=''
fi

# ========== Logging-Funktionen (MUSS vor Module laden definiert werden!) ==========
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

log_info() {
    log "INFO" "$@"
}

log_success() {
    log "SUCCESS" "$@"
}

log_error() {
    log "ERROR" "$@"
}

log_warning() {
    log "WARNING" "$@"
}

# ========== Module laden ==========
if [ ! -f "$SCRIPT_DIR/lib/statistics.sh" ]; then
    echo "$(t 'error_file_not_found') statistics.sh $(t 'error_not_found_in') $SCRIPT_DIR/lib/" >&2
    exit 1
fi
source "$SCRIPT_DIR/lib/i18n.sh"
source "$SCRIPT_DIR/lib/statistics.sh"
source "$SCRIPT_DIR/lib/progress.sh"
source "$SCRIPT_DIR/lib/interactive.sh"
source "$SCRIPT_DIR/lib/pre-check.sh"
source "$SCRIPT_DIR/lib/output.sh"
source "$SCRIPT_DIR/lib/summary.sh"

# ========== Kommandozeilen-Argumente ==========
INTERACTIVE_MODE=false

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --only-system)
                UPDATE_AUR=false
                UPDATE_CURSOR=false
                UPDATE_ADGUARD=false
                UPDATE_FLATPAK=false
                shift
                ;;
            --only-aur)
                UPDATE_SYSTEM=false
                UPDATE_CURSOR=false
                UPDATE_ADGUARD=false
                UPDATE_FLATPAK=false
                shift
                ;;
            --only-cursor)
                UPDATE_SYSTEM=false
                UPDATE_AUR=false
                UPDATE_ADGUARD=false
                UPDATE_FLATPAK=false
                shift
                ;;
            --only-adguard)
                UPDATE_SYSTEM=false
                UPDATE_AUR=false
                UPDATE_CURSOR=false
                UPDATE_FLATPAK=false
                shift
                ;;
            --only-flatpak)
                UPDATE_SYSTEM=false
                UPDATE_AUR=false
                UPDATE_CURSOR=false
                UPDATE_ADGUARD=false
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --interactive|-i)
                INTERACTIVE_MODE=true
                shift
                ;;
            --stats)
                show_stats
                exit 0
                ;;
            --help|-h)
                echo "$(t 'app_name')"
                echo "$(t 'version_label') $SCRIPT_VERSION"
                echo ""
                echo "$(t 'usage') $0 [OPTIONEN]"
                echo ""
                echo "$(t 'options')"
                echo "  --only-system        $(t 'only_system')"
                echo "  --only-aur           $(t 'only_aur')"
                echo "  --only-cursor        $(t 'only_cursor')"
                echo "  --only-adguard       $(t 'only_adguard')"
                echo "  --only-flatpak       $(t 'only_flatpak')"
                echo "  --dry-run            $(t 'dry_run_desc')"
                echo "  --interactive, -i    $(t 'interactive_desc')"
                echo "  --stats              $(t 'stats_desc')"
                echo "  --version, -v        $(t 'version_desc')"
                echo "  --help, -h           $(t 'help_desc')"
                echo ""
                exit 0
                ;;
            --version|-v)
                echo "$(t 'app_name') $(t 'version_label') $SCRIPT_VERSION"
                exit 0
                ;;
            *)
                echo "❌ $(t 'unknown_option') $1"
                echo "$(t 'use_help')"
                exit 1
                ;;
        esac
    done
}

parse_args "$@"

# Interaktiver Modus aktivieren
if [ "$INTERACTIVE_MODE" = "true" ]; then
    interactive_mode
fi

# ========== Dry-Run Anzeige ==========
if [ "$DRY_RUN" = "true" ]; then
    echo "🔍 $(t 'dry_run_mode')"
    echo ""
    echo "$(t 'planned_updates')"
    [ "$UPDATE_SYSTEM" = "true" ] && echo "  ✅ $(t 'system_updates')"
    [ "$UPDATE_AUR" = "true" ] && echo "  ✅ $(t 'aur_updates')"
    [ "$UPDATE_CURSOR" = "true" ] && echo "  ✅ $(t 'cursor_editor_update')"
    [ "$UPDATE_ADGUARD" = "true" ] && echo "  ✅ $(t 'adguard_home_update')"
    [ "$UPDATE_FLATPAK" = "true" ] && echo "  ✅ $(t 'flatpak_updates')"
    echo ""
fi

# Farben sind bereits oben gesetzt (vor Module laden)

# ========== Update-Zeitplanung prüfen ==========
check_update_frequency() {
    local last_update_file
    last_update_file=$(find "$LOG_DIR" -name "update-*.log" -type f 2>/dev/null | sort -r | head -1)

    if [ -z "$last_update_file" ]; then
        log_info "$(t 'log_no_previous_update')"
        return 0
    fi

    local last_update_time
    last_update_time=$(stat -c %Y "$last_update_file" 2>/dev/null || echo 0)
    local current_time
    current_time=$(date +%s)
    local days_ago=$(( (current_time - last_update_time) / 86400 ))

    if [ $days_ago -gt 14 ]; then
        log_warning "$(t 'log_last_update_days') $days_ago $(t 'days')! $(t 'log_regular_updates_recommended')"
        echo ""
        echo "⚠️  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "   $(t 'warning_last_update') $days_ago $(t 'days')!"
        echo "   $(t 'regular_updates_important')"
        echo "   $(t 'recommendation_weekly')"
        echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    elif [ $days_ago -gt 7 ]; then
        log_info "$(t 'log_last_update_days') $days_ago $(t 'days')"
        echo "ℹ️  $(t 'last_update_days_ago') $days_ago $(t 'days')"
    fi
}

# ========== Fehler-Report Generator ==========
generate_error_report() {
    local error_type="${1:-Unbekannt}"
    local error_file
    error_file="$LOG_DIR/error-report-$(date +%Y%m%d-%H%M%S).txt"

    {
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "$(t 'error_report_title')"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "$(t 'error_type')      $error_type"
        echo "$(t 'date_label')          $(date '+%Y-%m-%d %H:%M:%S')"
        echo "$(t 'script_version_label') $SCRIPT_VERSION"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "$(t 'system_information')"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "$(t 'os_label')        $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2 || echo "$(t 'unknown')")"
        echo "$(t 'kernel_label')    $(uname -r)"
        echo "$(t 'user_label')      $(whoami)"
        echo "$(t 'hostname_label')  $(hostname)"
        echo "$(t 'disk_label')      $(df -h / 2>/dev/null | awk 'NR==2 {print $4 " free / " $2 " total"}' || echo "N/A")"
        echo "$(t 'memory_label')    $(free -h 2>/dev/null | awk 'NR==2 {print $7 " available / " $2 " total"}' || echo "N/A")"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "$(t 'last_50_log_lines')"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        tail -50 "$LOG_FILE" 2>/dev/null || echo "$(t 'log_file_not_available')"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "$(t 'configuration')"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        if [ -f "$CONFIG_FILE" ]; then
            cat "$CONFIG_FILE"
        else
            echo "$(t 'no_config_file')"
        fi
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "$(t 'end_error_report')"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    } > "$error_file"

    log_error "$(t 'log_error_report_created') $error_file"
    echo ""
    echo "❌ $(t 'error_occurred')"
    echo "   $(t 'error_report_created') $error_file"
    echo "   $(t 'please_check_report')"
    echo ""
}

# ========== System-Info sammeln ==========
collect_system_info() {
    cat >> "$LOG_FILE" <<EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SYSTEM INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OS:             $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2 || echo "$(t 'unknown')")
Kernel:         $(uname -r)
Script Version: $SCRIPT_VERSION
Datum:          $(date '+%Y-%m-%d %H:%M:%S')
Benutzer:       $(whoami)
Hostname:       $(hostname)
Disk Space:     $(df -h / 2>/dev/null | awk 'NR==2 {print $4 " frei von " $2}' || echo "N/A")
Memory:         $(free -h 2>/dev/null | awk 'NR==2 {print $7 " verfügbar von " $2}' || echo "N/A")
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
}

# Logging-Funktionen sind bereits oben definiert (vor Module laden)

# ========== Error Handling ==========
cleanup_on_error() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "$(t 'log_script_error_exit') $exit_code)"
        notify-send "Update fehlgeschlagen!" "Bitte Logs prüfen: $LOG_FILE" 2>/dev/null || true
        # Terminal offen halten bei Fehlern
        if [ -t 0 ] && [ -t 1 ]; then
            echo ""
            read -p "Drücke Enter zum Beenden..." || true
        fi
    fi
    return $exit_code
}

trap cleanup_on_error EXIT

# ========== Retry-Funktion für Downloads ==========
download_with_retry() {
    local url="$1"
    local output_file="$2"
    local max_retries="${DOWNLOAD_RETRIES:-3}"
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        if curl -L -f --progress-bar -o "$output_file" "$url" 2>&1 | tee -a "$LOG_FILE"; then
            return 0
        fi
        
        retry=$((retry + 1))
        if [ $retry -lt $max_retries ]; then
            log_warning "$(t 'log_download_failed_retry') $retry/$max_retries..."
            sleep 2
        else
            log_error "$(t 'log_download_failed_after') $max_retries $(t 'log_attempts_failed')"
            return 1
        fi
    done
}

# ========== Alte Logs aufräumen ==========
cleanup_old_logs() {
    if [ -d "$LOG_DIR" ]; then
        # Zähle vorhandene Log-Dateien
        local log_count
        log_count=$(find "$LOG_DIR" -name "update-*.log" -type f 2>/dev/null | wc -l)
        
        # Wenn mehr als MAX_LOG_FILES vorhanden sind, lösche die ältesten
        if [ "$log_count" -gt "$MAX_LOG_FILES" ]; then
            local files_to_delete
            files_to_delete=$((log_count - MAX_LOG_FILES))
            log_info "Bereinige alte Log-Dateien: $files_to_delete von $log_count Dateien werden gelöscht (behält $MAX_LOG_FILES neueste)"
            find "$LOG_DIR" -name "update-*.log" -type f -printf '%T@ %p\n' 2>/dev/null | \
                sort -rn | \
                tail -n +$((MAX_LOG_FILES + 1)) | \
                cut -d' ' -f2- | \
                xargs rm -f 2>/dev/null || true
        fi
    fi
}

cleanup_old_logs

# System-Info sammeln
collect_system_info

# ========== System-Erkennung ==========
# Prüfe ob es eine Arch-basierte Distribution ist
check_arch_based() {
    if [ -f /etc/os-release ]; then
        local id=$(grep "^ID=" /etc/os-release | cut -d'=' -f2 | tr -d '"' || echo "")
        local id_like=$(grep "^ID_LIKE=" /etc/os-release | cut -d'=' -f2 | tr -d '"' || echo "")
        
        # Liste bekannter Arch-basierter Distributionen
        case "$id" in
            arch|archlinux|cachyos|manjaro|endeavouros|arcolinux|artix|garuda|rebornos|parabola)
                return 0
                ;;
        esac
        
        # Prüfe ID_LIKE für Arch-basierte Distributionen
        case "$id_like" in
            *arch*)
                return 0
                ;;
        esac
        
        # Wenn weder ID noch ID_LIKE Arch enthält, aber pacman vorhanden ist
        if command -v pacman >/dev/null 2>&1; then
            log_warning "$(t 'log_non_arch_detected') (ID: $id, ID_LIKE: $id_like)"
            log_warning "$(t 'log_pacman_found_continuing')"
            return 0
        fi
        
        return 1
    else
        # Fallback: Prüfe ob pacman vorhanden ist
        if command -v pacman >/dev/null 2>&1; then
            log_warning "$(t 'log_os_release_not_found')"
            log_warning "$(t 'log_pacman_found_continuing')"
            return 0
        fi
        return 1
    fi
}

# Prüfe System (nur Warnung, kein Abbruch)
if ! check_arch_based; then
    log_warning "$(t 'log_non_arch_system')"
    log_warning "$(t 'log_script_may_not_work')"
fi

log_info "$(t 'log_version') $SCRIPT_VERSION"
log_info "$(t 'log_update_started')"
log_info "$(t 'log_file') $LOG_FILE"
[ "$DRY_RUN" = "true" ] && log_info "$(t 'log_dry_run_enabled')"
[ "$ENABLE_COLORS" = "true" ] && log_info "$(t 'log_colors_enabled')"

# Prüfe Update-Häufigkeit
check_update_frequency

# Geschätzte Dauer anzeigen
estimate_duration

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${COLOR_BOLD}$(t 'app_name') v$SCRIPT_VERSION${COLOR_RESET}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Passwort-Abfrage VOR den Updates (damit Desktop-Icon funktioniert)
if [ "$DRY_RUN" != "true" ]; then
    echo -e "${COLOR_INFO}🔐 $(t 'sudo_required')${COLOR_RESET}"
    echo ""
    sudo -v || {
        log_error "$(t 'sudo_failed')"
        echo ""
        echo -e "${COLOR_ERROR}❌ $(t 'sudo_failed')${COLOR_RESET}"
        exit $EXIT_UPDATE_ERROR
    }
fi

# ========== PRE-UPDATE CHECK ==========
# Zeige verfügbare Updates BEVOR wir starten
check_available_updates

# Berechne Gesamtschritte für Fortschritts-Anzeige
TOTAL_STEPS=$(calculate_total_steps)
CURRENT_STEP=0

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${COLOR_BOLD}🚀 $(t 'update_process_starts')${COLOR_RESET}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ========== System-Updates (pacman) ==========
if [ "$UPDATE_SYSTEM" = "true" ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'system_updates')" "🔄"

    log_info "$(t 'log_starting_system_update')"
    show_system_update_start

    if [ "$DRY_RUN" = "true" ]; then
        packages_available=$(pacman -Qu 2>/dev/null | wc -l || echo "0")
        log_info "$(t 'log_dry_run_available_updates') $packages_available $(t 'packages')"
        log_info "$(t 'log_dry_run_would_execute') sudo pacman -Syu --noconfirm"
    else
        # Zähle Pakete VOR dem Update
        SYSTEM_PACKAGES=$(pacman -Qu 2>/dev/null | wc -l || echo "0")
        # Bereinige Newlines und Whitespace
        SYSTEM_PACKAGES=$(echo "$SYSTEM_PACKAGES" | tr -d '\n\r' | xargs)
        log_info "$(t 'log_packages_to_update') $SYSTEM_PACKAGES"
        # Debug: Liste der zu aktualisierenden Pakete
        if [ "$SYSTEM_PACKAGES" -gt 0 ]; then
            log_info "Pakete: $(pacman -Qu 2>/dev/null | head -5 | tr '\n' ',' | sed 's/,$//' || echo 'N/A')"
        fi

        # Führe Pacman-Update durch
        if sudo pacman -Syu --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
            SYSTEM_UPDATED=true
            log_success "$(t 'log_system_update_success') ($SYSTEM_PACKAGES $(t 'log_packages_updated'))"
            show_system_update_result "$SYSTEM_PACKAGES"
            show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'system_updates')" "✅"
        else
            log_error "$(t 'log_pacman_update_failed')"
            show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'system_updates')" "❌"
            exit $EXIT_UPDATE_ERROR
        fi
    fi
else
    log_info "$(t 'log_system_update_skipped')"
fi

# ========== AUR updaten ==========
if [ "$UPDATE_AUR" = "true" ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'aur_updates')" "🔄"

    log_info "$(t 'log_starting_aur_update')"
    show_aur_update_start

    if [ "$DRY_RUN" = "true" ]; then
        if command -v yay >/dev/null 2>&1; then
            log_info "$(t 'log_dry_run_would_execute') yay -Syu --noconfirm"
        elif command -v paru >/dev/null 2>&1; then
            log_info "$(t 'log_dry_run_would_execute') paru -Syu --noconfirm"
        else
            log_warning "$(t 'log_dry_run_no_aur_helper')"
        fi
    else
        if command -v yay >/dev/null 2>&1; then
            log_info "$(t 'log_using_yay')"
            AUR_PACKAGES=$(yay -Qua 2>/dev/null | wc -l || echo "0")
            if yay -Syu --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
                AUR_UPDATED=true
                log_success "$(t 'log_aur_update_success_yay')"
                
                # Entferne verwaiste AUR-Pakete (nicht mehr gepflegte Pakete)
                AUR_ORPHANS=$(yay -Qtd 2>/dev/null || true)
                if [ -n "$AUR_ORPHANS" ]; then
                    log_info "$(t 'log_removing_aur_orphans')"
                    ORPHAN_COUNT=$(echo "$AUR_ORPHANS" | wc -l)
                    echo "$AUR_ORPHANS" | while read -r orphan; do
                        if [ -n "$orphan" ]; then
                            log_info "Entferne verwaistes AUR-Paket: $orphan"
                            yay -Rns "$orphan" --noconfirm 2>&1 | tee -a "$LOG_FILE" || log_warning "Fehler beim Entfernen von $orphan"
                        fi
                    done
                    log_success "$(t 'log_aur_orphans_removed') ($ORPHAN_COUNT $(t 'packages'))"
                else
                    log_info "$(t 'log_no_aur_orphans')"
                fi
                
                show_aur_update_result "$AUR_PACKAGES"
                show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'aur_updates')" "✅"
            else
                log_warning "$(t 'log_aur_update_warnings_yay')"
                show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'aur_updates')" "⚠️"
            fi
        elif command -v paru >/dev/null 2>&1; then
            log_info "$(t 'log_using_paru')"
            AUR_PACKAGES=$(paru -Qua 2>/dev/null | wc -l || echo "0")
            if paru -Syu --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
                AUR_UPDATED=true
                log_success "$(t 'log_aur_update_success_paru')"
                
                # Entferne verwaiste AUR-Pakete (nicht mehr gepflegte Pakete)
                AUR_ORPHANS=$(paru -Qtd 2>/dev/null || true)
                if [ -n "$AUR_ORPHANS" ]; then
                    log_info "$(t 'log_removing_aur_orphans')"
                    ORPHAN_COUNT=$(echo "$AUR_ORPHANS" | wc -l)
                    echo "$AUR_ORPHANS" | while read -r orphan; do
                        if [ -n "$orphan" ]; then
                            log_info "Entferne verwaistes AUR-Paket: $orphan"
                            paru -Rns "$orphan" --noconfirm 2>&1 | tee -a "$LOG_FILE" || log_warning "Fehler beim Entfernen von $orphan"
                        fi
                    done
                    log_success "$(t 'log_aur_orphans_removed') ($ORPHAN_COUNT $(t 'packages'))"
                else
                    log_info "$(t 'log_no_aur_orphans')"
                fi
                
                show_aur_update_result "$AUR_PACKAGES"
                show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'aur_updates')" "✅"
            else
                log_warning "$(t 'log_aur_update_warnings_paru')"
                show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'aur_updates')" "⚠️"
            fi
        else
            log_warning "$(t 'log_no_aur_helper_found')"
            show_component_not_found "yay/paru"
            show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'aur_updates')" "⏭️"
        fi
    fi
else
    log_info "$(t 'log_aur_update_skipped')"
fi

# ========== Versionsvergleichsfunktion ==========
# Vergleicht zwei semantische Versionen (z.B. "2.0.77" vs "2.1.39")
# Gibt zurück: "newer", "older", oder "equal"
compare_versions() {
    local version1="$1"
    local version2="$2"
    
    # Entferne Build-Nummern (z.B. "2.1.39-1" -> "2.1.39")
    version1=$(echo "$version1" | sed 's/-.*$//')
    version2=$(echo "$version2" | sed 's/-.*$//')
    
    # Verwende sort -V für semantischen Versionsvergleich
    if [ "$version1" = "$version2" ]; then
        echo "equal"
    elif printf '%s\n%s\n' "$version1" "$version2" | sort -V | head -1 | grep -q "^$version1$"; then
        echo "older"
    else
        echo "newer"
    fi
}

# ========== Installationsmethode-Erkennung ==========
detect_cursor_installation_method() {
    # Gibt zurück: "pacman", "aur", oder "manual"
    if pacman -Q cursor 2>/dev/null | grep -q cursor; then
        echo "pacman"
    elif pacman -Q cursor-bin 2>/dev/null | grep -q cursor-bin; then
        echo "aur"
    else
        echo "manual"
    fi
}

detect_adguard_installation_method() {
    # Gibt zurück: "pacman", "aur", oder "manual"
    if pacman -Q adguard-home 2>/dev/null | grep -q adguard-home; then
        echo "pacman"
    elif pacman -Q adguard-home-bin 2>/dev/null | grep -q adguard-home-bin || pacman -Q adguardhome 2>/dev/null | grep -q adguardhome; then
        echo "aur"
    elif [[ -f "$HOME/AdGuardHome/AdGuardHome" ]]; then
        echo "manual"
    else
        echo "not_installed"
    fi
}

# ========== Cursor updaten ==========
if [ "$UPDATE_CURSOR" = "true" ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "🔄"

    log_info "$(t 'log_starting_cursor_update')"
    show_cursor_update_start
    
    if [ "$DRY_RUN" = "true" ]; then
        if command -v cursor >/dev/null 2>&1; then
            CURSOR_INSTALL_METHOD=$(detect_cursor_installation_method)
            log_info "[DRY-RUN] Cursor Installationsmethode: $CURSOR_INSTALL_METHOD"
            # Versuche package.json zu finden (ohne cursor --version aufzurufen!)
            CURSOR_PATH=$(which cursor)
            CURSOR_INSTALL_DIR=$(dirname "$(readlink -f "$CURSOR_PATH")")
            CURRENT_VERSION="unbekannt"
            if [ -f "$CURSOR_INSTALL_DIR/resources/app/package.json" ]; then
                CURRENT_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$CURSOR_INSTALL_DIR/resources/app/package.json" 2>/dev/null | head -1 || echo "unbekannt")
            fi
            log_info "[DRY-RUN] Aktuelle Cursor-Version: $CURRENT_VERSION"
            log_info "[DRY-RUN] Würde Cursor entsprechend der Installationsmethode aktualisieren"
        else
            log_warning "[DRY-RUN] Cursor nicht gefunden"
        fi
    elif ! command -v cursor >/dev/null 2>&1; then
        log_warning "Cursor nicht gefunden – bitte manuell installieren!"
        show_component_not_found "Cursor"
    else
        # Erkenne Installationsmethode
        CURSOR_INSTALL_METHOD=$(detect_cursor_installation_method)
        log_info "$(t 'log_cursor_install_method_detected') $CURSOR_INSTALL_METHOD"
        
        case "$CURSOR_INSTALL_METHOD" in
            "pacman")
                # Über pacman installiert → wird über System-Updates verwaltet
            CURSOR_PACMAN_VERSION=$(pacman -Q cursor | awk '{print $2}')
            log_info "Cursor ist über pacman installiert (Version: $CURSOR_PACMAN_VERSION)"
                log_info "Update-Methode: Wird über System-Updates (pacman -Syu) verwaltet"
            show_cursor_pacman_managed "$CURSOR_PACMAN_VERSION"
            log_info "Cursor-Update übersprungen (wird über pacman verwaltet)"
            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "⏭️"
                ;;
            "aur")
                # Über AUR installiert → prüfe ob Updates im AUR verfügbar sind
                CURSOR_AUR_VERSION_FULL=$(pacman -Q cursor-bin | awk '{print $2}')
                # Extrahiere Version ohne Build-Nummer (2.1.39-1 -> 2.1.39)
                CURSOR_AUR_VERSION=$(echo "$CURSOR_AUR_VERSION_FULL" | sed 's/-.*$//')
                log_info "$(t 'log_cursor_aur_installed') $CURSOR_AUR_VERSION_FULL)"
                log_info "$(t 'log_update_method_aur')"
                
                # Ermittle installierte Version aus package.json
                # Bei AUR-Installation ist package.json in /usr/share/cursor/resources/app/package.json
                # Priorität: AUR-Pfad zuerst, dann andere Pfade
                INSTALLED_VERSION=""
                for alt_path in "/usr/share/cursor/resources/app/package.json" "/opt/Cursor/resources/app/package.json" "/opt/cursor/resources/app/package.json" "$HOME/.local/share/cursor/resources/app/package.json"; do
                    if [ -f "$alt_path" ]; then
                        INSTALLED_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$alt_path" 2>/dev/null | head -1 || echo "")
                        [ -n "$INSTALLED_VERSION" ] && break
                    fi
                done
                # Fallback: Versuche über CURSOR_PATH
                if [ -z "$INSTALLED_VERSION" ]; then
                    CURSOR_PATH=$(which cursor)
                    CURSOR_INSTALL_DIR=$(dirname "$(readlink -f "$CURSOR_PATH")")
                    if [ -f "$CURSOR_INSTALL_DIR/resources/app/package.json" ]; then
                        INSTALLED_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$CURSOR_INSTALL_DIR/resources/app/package.json" 2>/dev/null | head -1 || echo "")
                    fi
                fi
                
                if [ -z "$INSTALLED_VERSION" ]; then
                    log_warning "$(t 'log_cursor_version_not_detectable')"
                    INSTALLED_VERSION="0.0.0"
                fi
                
                log_info "$(t 'log_installed_cursor_version') $INSTALLED_VERSION"
                log_info "$(t 'log_aur_cursor_version') $CURSOR_AUR_VERSION"
                
                # WICHTIG: Prüfe ob Updates im AUR verfügbar sind (nicht nur installierte Version vergleichen!)
                AUR_UPDATE_AVAILABLE=false
                if command -v yay >/dev/null 2>&1; then
                    AUR_UPDATE_CHECK=$(yay -Qua cursor-bin 2>/dev/null | grep -q cursor-bin && echo "yes" || echo "no")
                    if [ "$AUR_UPDATE_CHECK" = "yes" ]; then
                        AUR_UPDATE_AVAILABLE=true
                        # Extrahiere neue Version aus yay -Qua Ausgabe
                        AUR_UPDATE_LINE=$(yay -Qua cursor-bin 2>/dev/null | grep cursor-bin)
                        if [ -n "$AUR_UPDATE_LINE" ]; then
                            # Format: "aur/cursor-bin 2.1.46-1 -> 2.1.47-1"
                            CURSOR_AUR_NEW_VERSION=$(echo "$AUR_UPDATE_LINE" | awk '{print $3}' | sed 's/-.*$//')
                            log_info "$(t 'log_cursor_update_needed') $INSTALLED_VERSION -> $CURSOR_AUR_NEW_VERSION (AUR)"
                        fi
                    fi
                elif command -v paru >/dev/null 2>&1; then
                    AUR_UPDATE_CHECK=$(paru -Qua cursor-bin 2>/dev/null | grep -q cursor-bin && echo "yes" || echo "no")
                    if [ "$AUR_UPDATE_CHECK" = "yes" ]; then
                        AUR_UPDATE_AVAILABLE=true
                        # Extrahiere neue Version aus paru -Qua Ausgabe
                        AUR_UPDATE_LINE=$(paru -Qua cursor-bin 2>/dev/null | grep cursor-bin)
                        if [ -n "$AUR_UPDATE_LINE" ]; then
                            # Format: "aur/cursor-bin 2.1.46-1 -> 2.1.47-1"
                            CURSOR_AUR_NEW_VERSION=$(echo "$AUR_UPDATE_LINE" | awk '{print $3}' | sed 's/-.*$//')
                            log_info "$(t 'log_cursor_update_needed') $INSTALLED_VERSION -> $CURSOR_AUR_NEW_VERSION (AUR)"
                        fi
                    fi
                fi
                
                if [ "$AUR_UPDATE_AVAILABLE" = "true" ]; then
                    # Update über AUR
                    if command -v yay >/dev/null 2>&1; then
                        log_info "$(t 'log_using_yay')"
                        if yay -S cursor-bin --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
                            CURSOR_UPDATED=true
                            log_success "$(t 'log_cursor_updated_via_aur')"
                            # Nach Update: Neue Version aus package.json lesen
                            sleep 1
                            NEW_INSTALLED_VERSION=""
                            if [ -f "$CURSOR_INSTALL_DIR/resources/app/package.json" ]; then
                                NEW_INSTALLED_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$CURSOR_INSTALL_DIR/resources/app/package.json" 2>/dev/null | head -1 || echo "")
                            fi
                            if [ -z "$NEW_INSTALLED_VERSION" ]; then
                                for alt_path in "/opt/Cursor/resources/app/package.json" "/usr/share/cursor/resources/app/package.json" "$HOME/.local/share/cursor/resources/app/package.json"; do
                                    if [ -f "$alt_path" ]; then
                                        NEW_INSTALLED_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$alt_path" 2>/dev/null | head -1 || echo "")
                                        [ -n "$NEW_INSTALLED_VERSION" ] && break
                                    fi
                                done
                            fi
                            if [ -z "$NEW_INSTALLED_VERSION" ]; then
                                NEW_INSTALLED_VERSION="$CURSOR_AUR_VERSION"
                            fi
                            log_info "$(t 'log_installed_cursor_version') $NEW_INSTALLED_VERSION"
                            show_cursor_update_result "$INSTALLED_VERSION" "$NEW_INSTALLED_VERSION"
                            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "✅"
                        else
                            log_error "$(t 'log_cursor_aur_update_failed')"
                            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "❌"
                        fi
                    elif command -v paru >/dev/null 2>&1; then
                        log_info "$(t 'log_using_paru')"
                        if paru -S cursor-bin --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
                            CURSOR_UPDATED=true
                            log_success "$(t 'log_cursor_updated_via_aur')"
                            # Nach Update: Neue Version aus package.json lesen
                            # Bei AUR-Installation ist package.json in /usr/share/cursor/resources/app/package.json
                            sleep 1
                            NEW_INSTALLED_VERSION=""
                            # Priorität: AUR-Pfad zuerst, dann andere Pfade
                            for alt_path in "/usr/share/cursor/resources/app/package.json" "/opt/Cursor/resources/app/package.json" "/opt/cursor/resources/app/package.json" "$HOME/.local/share/cursor/resources/app/package.json"; do
                                if [ -f "$alt_path" ]; then
                                    NEW_INSTALLED_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$alt_path" 2>/dev/null | head -1 || echo "")
                                    [ -n "$NEW_INSTALLED_VERSION" ] && break
                                fi
                            done
                            # Fallback: Versuche über CURSOR_INSTALL_DIR
                            if [ -z "$NEW_INSTALLED_VERSION" ] && [ -n "$CURSOR_INSTALL_DIR" ]; then
                                if [ -f "$CURSOR_INSTALL_DIR/resources/app/package.json" ]; then
                                    NEW_INSTALLED_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$CURSOR_INSTALL_DIR/resources/app/package.json" 2>/dev/null | head -1 || echo "")
                                fi
                            fi
                            if [ -z "$NEW_INSTALLED_VERSION" ]; then
                                NEW_INSTALLED_VERSION="$CURSOR_AUR_VERSION"
                            fi
                            log_info "$(t 'log_installed_cursor_version') $NEW_INSTALLED_VERSION"
                            show_cursor_update_result "$INSTALLED_VERSION" "$NEW_INSTALLED_VERSION"
                            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "✅"
                        else
                            log_error "$(t 'log_cursor_aur_update_failed')"
                            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "❌"
                        fi
                    else
                        log_warning "$(t 'log_no_aur_helper_found')"
                        show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "⏭️"
                    fi
                else
                    log_info "$(t 'log_cursor_already_latest_aur')"
                    show_cursor_update_result "$INSTALLED_VERSION" "$INSTALLED_VERSION"
                    show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "✅"
                fi
                ;;
            "manual")
                # Manuell installiert → direktes Update
                log_info "$(t 'log_cursor_manual_installed')"
                log_info "$(t 'log_update_method_manual')"
                # Fahre mit Update-Prüfung fort
                ;;
        esac
        
        # Wenn manuell installiert, fahre mit direktem Update fort
        if [ "$CURSOR_INSTALL_METHOD" = "manual" ]; then
            # Cursor-Pfad finden
            CURSOR_PATH=$(which cursor)
            CURSOR_INSTALL_DIR=$(dirname "$(readlink -f "$CURSOR_PATH")")

            log_info "$(t 'log_cursor_found_in') $CURSOR_INSTALL_DIR"

            # Aktuelle Version ermitteln (nur package.json - --version öffnet Cursor!)
            CURRENT_VERSION=""
            # Methode 1: package.json (zuverlässigste Methode, öffnet Cursor nicht)
            if [ -f "$CURSOR_INSTALL_DIR/resources/app/package.json" ]; then
                CURRENT_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$CURSOR_INSTALL_DIR/resources/app/package.json" 2>/dev/null | head -1 || echo "")
            fi
            # Fallback: Prüfe alternative Pfade (falls Cursor anders installiert)
            if [ -z "$CURRENT_VERSION" ]; then
                # Versuche andere mögliche Pfade
                for alt_path in "/opt/Cursor/resources/app/package.json" "/usr/share/cursor/resources/app/package.json" "$HOME/.local/share/cursor/resources/app/package.json"; do
                    if [ -f "$alt_path" ]; then
                        CURRENT_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$alt_path" 2>/dev/null | head -1 || echo "")
                        [ -n "$CURRENT_VERSION" ] && break
                    fi
                done
            fi
            if [ -z "$CURRENT_VERSION" ]; then
                CURRENT_VERSION="unbekannt"
            fi
            log_info "$(t 'log_current_cursor_version') $CURRENT_VERSION"
            
            # Prüfe neueste verfügbare Version
            # WICHTIG: Cursor API gibt 404 zurück - nutze direkten Download von cursor.com
            # Vereinfachte Lösung: Prüfe ob Update nötig ist durch Dateigröße/Hash-Vergleich
            # Oder: Akzeptiere dass Versionsprüfung nicht perfekt ist und lade bei jedem Run
            # BESSER: Nutze GitHub Releases API falls verfügbar, sonst direkter Download
            SKIP_INSTALL=false
            DEB_FILE="$SCRIPT_DIR/cursor_latest_amd64.deb"
            # Direkter Download-Link von cursor.com (Linux .deb x64)
            # Siehe https://cursor.com/download - Linux .deb (x64)
            DOWNLOAD_URL="https://api2.cursor.sh/updates/download/golden/linux-x64-deb/cursor/2.0"
            
            # Versuche Version aus .deb zu extrahieren NACH Download
            if [ "$CURRENT_VERSION" != "unbekannt" ]; then
                log_info "$(t 'log_cursor_version_detected') $CURRENT_VERSION"
                
                # NEU: Versuche Version OHNE Download zu prüfen (HTTP HEAD Request)
                # Die API gibt einen Redirect mit Version im Dateinamen zurück
                log_info "$(t 'log_checking_version_http')"
                LOCATION_HEADER=$(curl -sI "$DOWNLOAD_URL" 2>/dev/null | grep -i "^location:" | cut -d' ' -f2- | tr -d '\r\n' || echo "")
                
                if [ -n "$LOCATION_HEADER" ]; then
                    # Extrahiere Version aus Dateinamen: cursor_2.0.69_amd64.deb -> 2.0.69
                    LATEST_VERSION=$(echo "$LOCATION_HEADER" | grep -oP 'cursor_(\K[0-9.]+)' | head -1 || echo "")

                    if [ -n "$LATEST_VERSION" ]; then
                        log_info "$(t 'log_latest_version_http') $LATEST_VERSION"

                        # Vergleiche Versionen
                        if [ "$CURRENT_VERSION" = "$LATEST_VERSION" ]; then
                            SKIP_INSTALL=true
                            log_info "$(t 'log_cursor_already_latest') ($CURRENT_VERSION)"
                            show_cursor_update_result "$CURRENT_VERSION" "$CURRENT_VERSION"
                            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "✅"
                        else
                            log_info "$(t 'log_update_available') $CURRENT_VERSION → $LATEST_VERSION"
                            show_cursor_update_downloading "$LATEST_VERSION"
                            # Download wird jetzt durchgeführt
                            log_info "$(t 'log_loading_cursor_deb_from') $DOWNLOAD_URL"
                            
                            if download_with_retry "$DOWNLOAD_URL" "$DEB_FILE"; then
                                if [[ -f "$DEB_FILE" ]] && [[ $(stat -c%s "$DEB_FILE") -gt 50000000 ]]; then
                                    DEB_SIZE=$(du -h "$DEB_FILE" | cut -f1)
                                    log_success "$(t 'log_download_successful') $DEB_SIZE"
                                else
                                    log_error "$(t 'log_download_too_small')"
                                    rm -f "$DEB_FILE"
                                    SKIP_INSTALL=true
                                    show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "❌"
                                fi
                            else
                                log_error "$(t 'log_cursor_download_failed')"
                                rm -f "$DEB_FILE"
                                SKIP_INSTALL=true
                                show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "❌"
                            fi
                        fi
                    else
                        log_warning "$(t 'log_version_extract_failed')"
                        echo "⬇️  $(t 'loading_cursor_deb')"
                        
                        if download_with_retry "$DOWNLOAD_URL" "$DEB_FILE"; then
                            if [[ -f "$DEB_FILE" ]] && [[ $(stat -c%s "$DEB_FILE") -gt 50000000 ]]; then
                                DEB_SIZE=$(du -h "$DEB_FILE" | cut -f1)
                                log_success "Download erfolgreich: $DEB_SIZE"
                                echo "✅ $(t 'download_successful') $DEB_SIZE"
                                
                                # Extrahiere Version aus .deb (Fallback-Methode)
                                TEMP_EXTRACT_DIR=$(mktemp -d -t cursor-version-check.XXXXXXXXXX)
                                if ! cd "$TEMP_EXTRACT_DIR" 2>/dev/null; then
                                    log_warning "$(t 'log_cannot_change_dir')"
                                    rm -rf "$TEMP_EXTRACT_DIR"
                                elif ! ar x "$DEB_FILE" 2>/dev/null; then
                                    cd "$SCRIPT_DIR" || true
                                    rm -rf "$TEMP_EXTRACT_DIR"
                                    log_warning "$(t 'log_extract_deb_failed')"
                                else
                                    # Finde die tar-Datei (kann .gz, .xz, .bz2 oder unkomprimiert sein)
                                    TAR_FILE=$(ls data.tar.* 2>/dev/null | head -1)
                                    if [ -z "$TAR_FILE" ]; then
                                        cd "$SCRIPT_DIR" || true
                                        rm -rf "$TEMP_EXTRACT_DIR"
                                        log_warning "$(t 'log_no_data_tar')"
                                    else
                                        # Versuche Extraktion mit verschiedenen Kompressionen
                                        EXTRACT_SUCCESS=false
                                        if [[ "$TAR_FILE" == *.gz ]]; then
                                            tar -xzf "$TAR_FILE" ./usr/share/cursor/resources/app/package.json 2>/dev/null || tar -xzf "$TAR_FILE" ./opt/cursor/resources/app/package.json 2>/dev/null
                                            EXTRACT_SUCCESS=$?
                                        elif [[ "$TAR_FILE" == *.xz ]]; then
                                            tar -xJf "$TAR_FILE" ./usr/share/cursor/resources/app/package.json 2>/dev/null || tar -xJf "$TAR_FILE" ./opt/cursor/resources/app/package.json 2>/dev/null
                                            EXTRACT_SUCCESS=$?
                                        elif [[ "$TAR_FILE" == *.bz2 ]]; then
                                            tar -xjf "$TAR_FILE" ./usr/share/cursor/resources/app/package.json 2>/dev/null || tar -xjf "$TAR_FILE" ./opt/cursor/resources/app/package.json 2>/dev/null
                                            EXTRACT_SUCCESS=$?
                                        else
                                            tar -xf "$TAR_FILE" ./usr/share/cursor/resources/app/package.json 2>/dev/null || tar -xf "$TAR_FILE" ./opt/cursor/resources/app/package.json 2>/dev/null
                                            EXTRACT_SUCCESS=$?
                                        fi
                                        
                                        if [ $EXTRACT_SUCCESS -eq 0 ]; then
                                            PACKAGE_JSON=""
                                            if [ -f "usr/share/cursor/resources/app/package.json" ]; then
                                                PACKAGE_JSON="usr/share/cursor/resources/app/package.json"
                                            elif [ -f "opt/cursor/resources/app/package.json" ]; then
                                                PACKAGE_JSON="opt/cursor/resources/app/package.json"
                                            fi
                                            
                                            if [ -n "$PACKAGE_JSON" ] && [ -f "$PACKAGE_JSON" ]; then
                                                LATEST_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$PACKAGE_JSON" 2>/dev/null | head -1 || echo "")
                                                cd "$SCRIPT_DIR" || true
                                                rm -rf "$TEMP_EXTRACT_DIR"
                                                
                                                if [ -n "$LATEST_VERSION" ]; then
                                                    log_info "$(t 'log_latest_version_from_deb') $LATEST_VERSION"
                                                    echo "📌 $(t 'available_version') $LATEST_VERSION"
                                                    
                                                    # Vergleiche Versionen
                                                    if [ "$CURRENT_VERSION" = "$LATEST_VERSION" ]; then
                                                        SKIP_INSTALL=true
                                                        log_info "$(t 'log_cursor_already_latest') ($CURRENT_VERSION)"
                                                        echo "✅ $(t 'cursor_already_current') ($CURRENT_VERSION)"
                                                        rm -f "$DEB_FILE"
                                                    else
                                                        log_info "$(t 'log_update_available') $CURRENT_VERSION → $LATEST_VERSION"
                                                        echo "🔄 $(t 'update_available_from_to') $CURRENT_VERSION → $LATEST_VERSION"
                                                    fi
                                                else
                                                    log_warning "$(t 'log_version_extract_package_json_failed')"
                                                fi
                                            else
                                                cd "$SCRIPT_DIR" || true
                                                rm -rf "$TEMP_EXTRACT_DIR"
                                                log_warning "$(t 'log_package_json_not_found')"
                                            fi
                                        else
                                            cd "$SCRIPT_DIR" || true
                                            rm -rf "$TEMP_EXTRACT_DIR"
                                            log_warning "$(t 'log_extract_tar_failed')"
                                        fi
                                    fi
                                    cd "$SCRIPT_DIR" || true
                                fi
                            else
                                log_error "Download zu klein oder fehlgeschlagen!"
                                echo "❌ $(t 'download_failed')"
                                rm -f "$DEB_FILE"
                                SKIP_INSTALL=true
                            fi
                        else
                            log_error "Cursor-Download fehlgeschlagen!"
                            echo "❌ Download fehlgeschlagen!"
                            rm -f "$DEB_FILE"
                            SKIP_INSTALL=true
                        fi
                    fi
                else
                    log_warning "$(t 'log_http_head_failed')"
                    echo "⬇️  $(t 'loading_cursor_deb')"
                    
                    if download_with_retry "$DOWNLOAD_URL" "$DEB_FILE"; then
                        if [[ -f "$DEB_FILE" ]] && [[ $(stat -c%s "$DEB_FILE") -gt 50000000 ]]; then
                            DEB_SIZE=$(du -h "$DEB_FILE" | cut -f1)
                            log_success "Download erfolgreich: $DEB_SIZE"
                            echo "✅ Download erfolgreich: $DEB_SIZE"
                            
                            # Extrahiere Version aus .deb (Fallback)
                            TEMP_EXTRACT_DIR=$(mktemp -d -t cursor-version-check.XXXXXXXXXX)
                            if ! cd "$TEMP_EXTRACT_DIR" 2>/dev/null; then
                                log_warning "Konnte nicht in temporäres Verzeichnis wechseln, fahre mit Installation fort..."
                                rm -rf "$TEMP_EXTRACT_DIR"
                            elif ! ar x "$DEB_FILE" 2>/dev/null; then
                                cd "$SCRIPT_DIR" || true
                                rm -rf "$TEMP_EXTRACT_DIR"
                                log_warning "Fehler beim Extrahieren der .deb-Datei, fahre mit Installation fort..."
                            else
                                TAR_FILE=$(ls data.tar.* 2>/dev/null | head -1)
                                if [ -z "$TAR_FILE" ]; then
                                    cd "$SCRIPT_DIR" || true
                                    rm -rf "$TEMP_EXTRACT_DIR"
                                    log_warning "Keine data.tar.* Datei gefunden, fahre mit Installation fort..."
                                else
                                    EXTRACT_SUCCESS=false
                                    if [[ "$TAR_FILE" == *.gz ]]; then
                                        tar -xzf "$TAR_FILE" ./usr/share/cursor/resources/app/package.json 2>/dev/null || tar -xzf "$TAR_FILE" ./opt/cursor/resources/app/package.json 2>/dev/null
                                        EXTRACT_SUCCESS=$?
                                    elif [[ "$TAR_FILE" == *.xz ]]; then
                                        tar -xJf "$TAR_FILE" ./usr/share/cursor/resources/app/package.json 2>/dev/null || tar -xJf "$TAR_FILE" ./opt/cursor/resources/app/package.json 2>/dev/null
                                        EXTRACT_SUCCESS=$?
                                    elif [[ "$TAR_FILE" == *.bz2 ]]; then
                                        tar -xjf "$TAR_FILE" ./usr/share/cursor/resources/app/package.json 2>/dev/null || tar -xjf "$TAR_FILE" ./opt/cursor/resources/app/package.json 2>/dev/null
                                        EXTRACT_SUCCESS=$?
                                    else
                                        tar -xf "$TAR_FILE" ./usr/share/cursor/resources/app/package.json 2>/dev/null || tar -xf "$TAR_FILE" ./opt/cursor/resources/app/package.json 2>/dev/null
                                        EXTRACT_SUCCESS=$?
                                    fi
                                    
                                    if [ $EXTRACT_SUCCESS -eq 0 ]; then
                                        PACKAGE_JSON=""
                                        if [ -f "usr/share/cursor/resources/app/package.json" ]; then
                                            PACKAGE_JSON="usr/share/cursor/resources/app/package.json"
                                        elif [ -f "opt/cursor/resources/app/package.json" ]; then
                                            PACKAGE_JSON="opt/cursor/resources/app/package.json"
                                        fi
                                        
                                        if [ -n "$PACKAGE_JSON" ] && [ -f "$PACKAGE_JSON" ]; then
                                            LATEST_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$PACKAGE_JSON" 2>/dev/null | head -1 || echo "")
                                            cd "$SCRIPT_DIR" || true
                                            rm -rf "$TEMP_EXTRACT_DIR"
                                            
                                            if [ -n "$LATEST_VERSION" ]; then
                                                log_info "Neueste verfügbare Version (aus .deb): $LATEST_VERSION"
                                                echo "📌 Verfügbare Version: $LATEST_VERSION"
                                                
                                                if [ "$CURRENT_VERSION" = "$LATEST_VERSION" ]; then
                                                    SKIP_INSTALL=true
                                                    log_info "Cursor ist bereits auf neuester Version ($CURRENT_VERSION)"
                                                    echo "✅ Cursor ist bereits aktuell ($CURRENT_VERSION)"
                                                    rm -f "$DEB_FILE"
                                                else
                                                    log_info "Update verfügbar: $CURRENT_VERSION → $LATEST_VERSION"
                                                    echo "🔄 Update verfügbar: $CURRENT_VERSION → $LATEST_VERSION"
                                                fi
                                            else
                                                log_warning "Version konnte nicht aus package.json extrahiert werden, fahre mit Installation fort..."
                                            fi
                                        else
                                            cd "$SCRIPT_DIR" || true
                                            rm -rf "$TEMP_EXTRACT_DIR"
                                            log_warning "package.json nicht in .deb gefunden, fahre mit Installation fort..."
                                        fi
                                    else
                                        cd "$SCRIPT_DIR" || true
                                        rm -rf "$TEMP_EXTRACT_DIR"
                                        log_warning "Fehler beim Extrahieren der tar-Datei, fahre mit Installation fort..."
                                    fi
                                fi
                                cd "$SCRIPT_DIR" || true
                            fi
                        else
                            log_error "Download zu klein oder fehlgeschlagen!"
                            echo "❌ Download fehlgeschlagen!"
                            rm -f "$DEB_FILE"
                            SKIP_INSTALL=true
                        fi
                    else
                        log_error "Cursor-Download fehlgeschlagen!"
                        echo "❌ Download fehlgeschlagen!"
                        rm -f "$DEB_FILE"
                        SKIP_INSTALL=true
                    fi
                fi
            else
                log_warning "$(t 'log_cursor_version_unknown')"
                echo "⬇️  $(t 'loading_cursor_deb_simple')"
                if ! download_with_retry "$DOWNLOAD_URL" "$DEB_FILE"; then
                    log_error "Cursor-Download fehlgeschlagen!"
                    echo "❌ Download fehlgeschlagen!"
                    rm -f "$DEB_FILE"
                    SKIP_INSTALL=true
                else
                    if [[ -f "$DEB_FILE" ]] && [[ $(stat -c%s "$DEB_FILE") -gt 50000000 ]]; then
                        DEB_SIZE=$(du -h "$DEB_FILE" | cut -f1)
                        log_success "Download erfolgreich: $DEB_SIZE"
                        echo "✅ Download erfolgreich: $DEB_SIZE"
                    else
                        log_error "Download zu klein oder fehlgeschlagen!"
                        echo "❌ Download fehlgeschlagen!"
                        rm -f "$DEB_FILE"
                        SKIP_INSTALL=true
                    fi
                fi
            fi
            
            # Überspringe Installation wenn bereits aktuell
            if [ "$SKIP_INSTALL" = "true" ]; then
                log_info "$(t 'log_cursor_update_skipped_current')"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                echo ""
            else
                # .deb wurde bereits heruntergeladen, fahre mit Installation fort
                if [[ -f "$DEB_FILE" ]] && [[ $(stat -c%s "$DEB_FILE") -gt 50000000 ]]; then
                    # Cursor-Prozesse prüfen (nicht automatisch schließen)
                    # Verwende -x für exact match, verhindert false positives
                    cursor_pids=$(pgrep -x "cursor" 2>/dev/null || pgrep -x "Cursor" 2>/dev/null || true)
                    if [ -n "$cursor_pids" ]; then
                        log_warning "$(t 'log_cursor_running_pid') $cursor_pids) - $(t 'log_please_close_manually')"
                        echo "⚠️  $(t 'cursor_running') $cursor_pids)"
                        echo "   $(t 'please_close_manually')"
                        echo "   $(t 'cursor_not_auto_closed')"
                    else
                        log_info "$(t 'log_no_cursor_processes')"
                        echo "ℹ️  $(t 'cursor_not_running')"
                    fi
                    
                    # Extrahiere .deb
                    extract_dir=$(mktemp -d -t cursor-extract.XXXXXXXXXX)
                    trap 'rm -rf "$extract_dir" "$DEB_FILE"' EXIT

                    log_info "$(t 'log_extracting_cursor_deb')"
                    show_cursor_update_installing
                    cd "$extract_dir"

                    if ! ar x "$DEB_FILE" 2>&1 | tee -a "$LOG_FILE"; then
                        log_error "$(t 'log_error_extracting_deb')"
                        echo "❌ Fehler beim Extrahieren!"
                        rm -rf "$extract_dir" "$DEB_FILE"
                        exit $EXIT_DOWNLOAD_ERROR
                    elif ! tar -xf data.tar.* 2>&1 | tee -a "$LOG_FILE"; then
                        log_error "$(t 'log_error_extracting_data')"
                        echo "❌ Fehler beim Extrahieren der Daten!"
                        rm -rf "$extract_dir" "$DEB_FILE"
                        exit $EXIT_DOWNLOAD_ERROR
                    else
                        # Finde Cursor-Binary und Ressourcen
                        install_success=false

                        if [[ -d "opt/Cursor" ]]; then
                            log_info "$(t 'log_installing_cursor_opt')"
                            show_cursor_update_installing
                            if sudo cp -rf opt/Cursor/* "$CURSOR_INSTALL_DIR/" 2>&1 | tee -a "$LOG_FILE"; then
                                sudo chmod +x "$CURSOR_INSTALL_DIR/cursor" 2>/dev/null || true
                                log_success "$(t 'log_cursor_update_installed')"
                                install_success=true
                            elif sudo cp -rf opt/Cursor/* "$(dirname "$CURSOR_INSTALL_DIR")/" 2>&1 | tee -a "$LOG_FILE"; then
                                sudo chmod +x "$(dirname "$CURSOR_INSTALL_DIR")/cursor" 2>/dev/null || true
                                log_success "$(t 'log_cursor_update_installed_alt')"
                                install_success=true
                            elif sudo cp -rf opt/Cursor /opt/ 2>&1 | tee -a "$LOG_FILE"; then
                                sudo chmod +x /opt/Cursor/cursor 2>/dev/null || true
                                log_success "$(t 'log_cursor_update_installed_opt')"
                                install_success=true
                            fi
                        elif [[ -d "usr/share/cursor" ]]; then
                            log_info "$(t 'log_installing_cursor_usr')"
                            show_cursor_update_installing
                            if sudo cp -rf usr/share/cursor/* "$CURSOR_INSTALL_DIR/" 2>&1 | tee -a "$LOG_FILE"; then
                                sudo chmod +x "$CURSOR_INSTALL_DIR/cursor" 2>/dev/null || true
                                log_success "$(t 'log_cursor_update_installed')"
                                install_success=true
                            fi
                        fi

                        # Cleanup IMMER durchführen (trap entfernen vor cleanup)
                        trap - EXIT
                        log_info "$(t 'log_cleaning_temp_files')"
                        rm -rf "$extract_dir" "$DEB_FILE"
                        log_info "$(t 'log_temp_files_deleted')"

                        if [ "$install_success" = "true" ]; then
                            # Neue Version prüfen (nur package.json - --version öffnet Cursor!)
                            sleep 1
                            NEW_VERSION="installiert"
                            if [ -f "$CURSOR_INSTALL_DIR/resources/app/package.json" ]; then
                                NEW_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$CURSOR_INSTALL_DIR/resources/app/package.json" 2>/dev/null | head -1 || echo "installiert")
                            fi
                            CURSOR_UPDATED=true
                            log_success "$(t 'log_cursor_updated') $CURRENT_VERSION → $NEW_VERSION"
                            show_cursor_update_result "$CURRENT_VERSION" "$NEW_VERSION"
                            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "✅"
                        else
                            log_error "$(t 'log_cursor_files_not_found')"
                            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "❌"
                        fi
                    fi
                    # WICHTIG: cd zurück zum Script-Verzeichnis
                    cd "$SCRIPT_DIR" || true
                else
                    log_error "Download zu klein oder fehlgeschlagen!"
                    echo "❌ $(t 'download_too_small')"
                    rm -f "$DEB_FILE"
                fi
            fi
        fi
    fi
fi

# ========== AdGuardHome updaten ==========
if [ "$UPDATE_ADGUARD" = "true" ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress $CURRENT_STEP $TOTAL_STEPS "AdGuard Home Update" "🔄"

    log_info "$(t 'log_starting_adguard_update')"
    show_adguard_update_start
    
    # Erkenne Installationsmethode
    ADGUARD_INSTALL_METHOD=$(detect_adguard_installation_method)
    log_info "$(t 'log_adguard_method_detected') $ADGUARD_INSTALL_METHOD"
    
    temp_dir=$(mktemp -d -t adguard-update.XXXXXXXXXX)
    trap 'rm -rf "$temp_dir"' EXIT
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "$(t 'log_dry_run_adguard_method') $ADGUARD_INSTALL_METHOD"
        case "$ADGUARD_INSTALL_METHOD" in
            "pacman"|"aur")
                log_info "$(t 'log_dry_run_package_manager')"
                ;;
            "manual")
                if [[ -f "$HOME/AdGuardHome/AdGuardHome" ]]; then
                    current_version=$(cd "$HOME/AdGuardHome" && ./AdGuardHome --version 2>/dev/null | grep -oP 'v\K[0-9.]+' || echo "0.0.0")
                    log_info "$(t 'log_dry_run_adguard_version') v$current_version"
                    log_info "$(t 'log_dry_run_adguard_direct')"
                else
                    log_warning "$(t 'log_dry_run_adguard_not_found')"
                fi
                ;;
            "not_installed")
                log_warning "$(t 'log_dry_run_adguard_not_installed')"
                ;;
        esac
    else
        case "$ADGUARD_INSTALL_METHOD" in
            "pacman")
                # Über pacman installiert → wird über System-Updates verwaltet
                ADGUARD_PACMAN_VERSION=$(pacman -Q adguard-home | awk '{print $2}')
                log_info "$(t 'log_adguard_pacman_installed') $ADGUARD_PACMAN_VERSION)"
                log_info "$(t 'log_adguard_update_method_pacman')"
                echo -e "${COLOR_WARNING}  ○ $(t 'managed_by_pacman') (v$ADGUARD_PACMAN_VERSION)${COLOR_RESET}"
                echo ""
                log_info "AdGuard Home-Update übersprungen (wird über pacman verwaltet)"
                show_progress $CURRENT_STEP $TOTAL_STEPS "AdGuard Home Update" "⏭️"
                ;;
            "aur")
                # Über AUR installiert → wird über AUR-Updates verwaltet
                ADGUARD_AUR_VERSION=$(pacman -Q adguard-home-bin 2>/dev/null | awk '{print $2}' || pacman -Q adguardhome 2>/dev/null | awk '{print $2}')
                log_info "$(t 'log_adguard_aur_installed') $ADGUARD_AUR_VERSION)"
                log_info "$(t 'log_adguard_update_method_aur')"
                echo -e "${COLOR_WARNING}  ○ $(t 'managed_by_pacman') (v$ADGUARD_AUR_VERSION, AUR)${COLOR_RESET}"
                echo ""
                log_info "AdGuard Home-Update übersprungen (wird über AUR verwaltet)"
                show_progress $CURRENT_STEP $TOTAL_STEPS "AdGuard Home Update" "⏭️"
                ;;
            "manual")
                # Manuell installiert → direktes Update
                agh_dir="$HOME/AdGuardHome"
                log_info "$(t 'log_adguard_manual_installed')"
                log_info "$(t 'log_adguard_update_method_manual')"
                
                if [[ -f "$agh_dir/AdGuardHome" ]]; then
        cd "$agh_dir"
        
        log_info "$(t 'log_stopping_adguard_service')"
        systemctl --user stop AdGuardHome 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_adguard_service_stop_failed')"

        current_version=$(./AdGuardHome --version 2>/dev/null | grep -oP 'v\K[0-9.]+' || echo "0.0.0")
        log_info "$(t 'log_current_adguard_version') v$current_version"

        # Prüfe neueste Version über GitHub Releases API
        log_info "$(t 'log_checking_adguard_version')"
        latest_version_gh=$(curl -s "https://api.github.com/repos/AdguardTeam/AdGuardHome/releases/latest" 2>/dev/null | grep -oP '"tag_name":\s*"v\K[0-9.]+' | head -1 || echo "")

        # Entferne 'v' Präfix falls vorhanden
        if [ -n "$latest_version_gh" ]; then
            latest_version_gh=$(echo "$latest_version_gh" | sed 's/^v//')
            log_info "$(t 'log_latest_adguard_version') v$latest_version_gh"

            # Versionsvergleich - wenn bereits aktuell, überspringe Download
            if [ "$current_version" = "$latest_version_gh" ]; then
                log_info "$(t 'log_adguard_already_latest') (v$current_version)"
                show_adguard_update_result "$current_version" "$current_version"
                ADGUARD_UPDATED=false
                show_progress $CURRENT_STEP $TOTAL_STEPS "AdGuard Home Update" "✅"
            else
                log_info "$(t 'log_adguard_update_available') v$current_version → v$latest_version_gh"
                show_adguard_update_downloading "$latest_version_gh"
                
                backup_dir="$agh_dir-backup-$(date +%Y%m%d-%H%M%S)"
                mkdir -p "$backup_dir"
                cp AdGuardHome.yaml data/* "$backup_dir/" 2>/dev/null || log_warning "$(t 'log_backup_failed')"
                log_info "$(t 'log_backup_created') $backup_dir"

                # Offizieller Download-Link von AdGuard (siehe https://adguard-dns.io/kb/de/adguard-home/getting-started/)
                download_url="https://static.adguard.com/adguardhome/release/AdGuardHome_linux_amd64.tar.gz"
                log_info "$(t 'log_loading_adguard_from') $download_url"

                if download_with_retry "$download_url" "$temp_dir/AdGuardHome.tar.gz"; then
                    if [[ -f "$temp_dir/AdGuardHome.tar.gz" ]]; then
                        if tar -C "$temp_dir" -xzf "$temp_dir/AdGuardHome.tar.gz" 2>&1 | tee -a "$LOG_FILE"; then
                            new_binary="$temp_dir/AdGuardHome/AdGuardHome"
                            if [[ -f "$new_binary" ]]; then
                                new_version=$("$new_binary" --version 2>/dev/null | grep -oP 'v\K[0-9.]+' || echo "0.0.0")
                                if [ "$new_version" != "$current_version" ]; then
                                    if cp "$new_binary" "$agh_dir/" 2>&1 | tee -a "$LOG_FILE"; then
                                        ADGUARD_UPDATED=true
                                        log_success "$(t 'adguard_updated') v$current_version → v$new_version"
                                        echo "✅ $(t 'adguard_updated') v$current_version → v$new_version"
                                    else
                                        log_error "$(t 'log_error_copying_adguard')"
                                    fi
                                else
                                    log_info "$(t 'log_adguard_already_current') (v$new_version)"
                                    echo "ℹ️ $(t 'adguard_current') (v$new_version)."
                                fi
                            else
                                log_error "$(t 'log_adguard_binary_not_found')"
                            fi
                        else
                            log_error "$(t 'log_error_extracting_adguard')"
                        fi
                    else
                        log_error "$(t 'log_adguard_download_failed')"
                    fi
                else
                    log_error "$(t 'log_adguard_download_failed')"
                fi
            fi
        else
            # Fallback: Alte Methode wenn GitHub API nicht verfügbar
            log_warning "GitHub API nicht verfügbar, verwende direkten Download..."
            backup_dir="$agh_dir-backup-$(date +%Y%m%d-%H%M%S)"
            mkdir -p "$backup_dir"
            cp AdGuardHome.yaml data/* "$backup_dir/" 2>/dev/null || log_warning "Backup konnte nicht erstellt werden"
            log_info "Backup erstellt in: $backup_dir"

            download_url="https://static.adguard.com/adguardhome/release/AdGuardHome_linux_amd64.tar.gz"
            log_info "Lade AdGuardHome von: $download_url"

            if download_with_retry "$download_url" "$temp_dir/AdGuardHome.tar.gz"; then
                if [[ -f "$temp_dir/AdGuardHome.tar.gz" ]]; then
                    if tar -C "$temp_dir" -xzf "$temp_dir/AdGuardHome.tar.gz" 2>&1 | tee -a "$LOG_FILE"; then
                        new_binary="$temp_dir/AdGuardHome/AdGuardHome"
                        if [[ -f "$new_binary" ]]; then
                            new_version=$("$new_binary" --version 2>/dev/null | grep -oP 'v\K[0-9.]+' || echo "0.0.0")
                            if [ "$new_version" != "$current_version" ]; then
                                if cp "$new_binary" "$agh_dir/" 2>&1 | tee -a "$LOG_FILE"; then
                                    ADGUARD_UPDATED=true
                                    log_success "AdGuardHome updated: v$current_version → v$new_version"
                                    show_adguard_update_result "$current_version" "$new_version"
                                    show_progress $CURRENT_STEP $TOTAL_STEPS "AdGuard Home Update" "✅"
                                else
                                    log_error "Fehler beim Kopieren der neuen AdGuardHome-Binary"
                                    show_progress $CURRENT_STEP $TOTAL_STEPS "AdGuard Home Update" "❌"
                                fi
                            else
                                log_info "AdGuardHome ist bereits aktuell (v$new_version)"
                                show_adguard_update_result "$new_version" "$new_version"
                                show_progress $CURRENT_STEP $TOTAL_STEPS "AdGuard Home Update" "✅"
                            fi
                        else
                            log_error "AdGuardHome-Binary nicht im Archiv gefunden"
                        fi
                    else
                        log_error "Fehler beim Extrahieren von AdGuardHome"
                    fi
                else
                    log_error "$(t 'log_adguard_download_failed')"
                fi
            else
                log_error "AdGuardHome-Download fehlgeschlagen!"
            fi
        fi
        rm -rf "$temp_dir"

        log_info "$(t 'log_starting_adguard_service')"
        if systemctl --user start AdGuardHome 2>&1 | tee -a "$LOG_FILE"; then
            sleep 2
            if systemctl --user is-active --quiet AdGuardHome; then
                log_success "$(t 'log_adguard_service_running')"
            else
                log_warning "$(t 'log_adguard_service_status_unclear')"
            fi
        else
            log_warning "$(t 'log_adguard_service_start_failed')"
        fi
    else
                    log_warning "$(t 'log_adguard_binary_not_found_path') $agh_dir"
                    echo "⚠️ $(t 'adguard_not_found') $agh_dir"
                fi
                ;;
            "not_installed")
                log_warning "AdGuard Home nicht installiert"
                show_component_not_found "AdGuard Home"
                show_progress $CURRENT_STEP $TOTAL_STEPS "AdGuard Home Update" "⏭️"
                ;;
        esac
    fi
else
    log_info "AdGuard Home-Update übersprungen (deaktiviert)"
fi

# ========== Flatpak updaten ==========
if [ "$UPDATE_FLATPAK" = "true" ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress $CURRENT_STEP $TOTAL_STEPS "Flatpak-Updates" "🔄"

    log_info "$(t 'log_starting_flatpak_update')"
    show_flatpak_update_start
    
    if [ "$DRY_RUN" = "true" ]; then
        if command -v flatpak >/dev/null 2>&1; then
            log_info "$(t 'log_dry_run_would_execute') flatpak update --noninteractive -y"
            FLATPAK_PACKAGES=$(flatpak remote-ls --updates 2>/dev/null | wc -l || echo "0")
            log_info "$(t 'log_dry_run_available_updates') $FLATPAK_PACKAGES $(t 'packages')"
        else
            log_warning "$(t 'log_dry_run_no_aur_helper')"
        fi
    else
        if command -v flatpak >/dev/null 2>&1; then
            # Prüfe verfügbare Updates
            FLATPAK_UPDATES=$(flatpak remote-ls --updates 2>/dev/null | wc -l || echo "0")
            FLATPAK_UPDATES=$(echo "$FLATPAK_UPDATES" | tr -d '\n\r' | xargs)
            log_info "$(t 'log_flatpak_updates_available') $FLATPAK_UPDATES $(t 'packages')"


            if [ "$FLATPAK_UPDATES" -gt 0 ] 2>/dev/null; then
                # Verwende --noninteractive für vollständig automatische Updates
                # WICHTIG: Prüfe Exit-Code, nicht grep-Output (flatpak gibt "Nichts zu tun." aus wenn keine Updates)
                FLATPAK_OUTPUT=$(flatpak update --noninteractive -y 2>&1 | tee -a "$LOG_FILE")
                FLATPAK_EXIT_CODE=$?
                if [ $FLATPAK_EXIT_CODE -eq 0 ]; then
                    FLATPAK_UPDATED=true
                    FLATPAK_PACKAGES="$FLATPAK_UPDATES"
                    log_success "$(t 'log_flatpak_update_success') ($FLATPAK_UPDATES $(t 'log_flatpak_updates_updated'))"
                    show_flatpak_update_result "$FLATPAK_UPDATES"
                    show_progress $CURRENT_STEP $TOTAL_STEPS "Flatpak-Updates" "✅"
                else
                    log_warning "$(t 'log_flatpak_update_warnings')"
                    show_progress $CURRENT_STEP $TOTAL_STEPS "Flatpak-Updates" "⚠️"
                fi
            else
                log_info "$(t 'log_no_flatpak_updates')"
                show_flatpak_update_result 0
                FLATPAK_PACKAGES=0
                show_progress $CURRENT_STEP $TOTAL_STEPS "Flatpak-Updates" "✅"
            fi
        else
            log_warning "$(t 'log_flatpak_not_found')"
            show_component_not_found "Flatpak"
            show_progress $CURRENT_STEP $TOTAL_STEPS "Flatpak-Updates" "⏭️"
        fi
    fi
else
    log_info "$(t 'log_flatpak_update_skipped')"
fi

# ========== Cleanup ==========
if [ "$DRY_RUN" = "true" ]; then
    log_info "[DRY-RUN] Würde System-Cleanup durchführen"
    log_info "[DRY-RUN] Würde ausführen: paccache -rk3"
    log_info "[DRY-RUN] Würde ausführen: sudo pacman -Sc --noconfirm"
    log_info "[DRY-RUN] Würde ausführen: flatpak uninstall --unused --noninteractive -y"
    log_info "[DRY-RUN] Würde verbleibende .deb Dateien und temporäre Verzeichnisse entfernen"
else
    log_info "$(t 'log_starting_cleanup')"
    show_cleanup_start
    
    # Alte Paketversionen im Cache behalten (nur die letzten 3 Versionen)
    log_info "$(t 'log_cleaning_package_cache')"
    paccache -rk3 2>&1 | tee -a "$LOG_FILE" || log_warning "Paccache fehlgeschlagen"
    
    # Entferne alte/deinstallierte Pakete aus dem Cache
    log_info "$(t 'log_removing_old_packages')"
    if yes | sudo pacman -Sc --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
        log_success "$(t 'log_package_cache_cleaned')"
    else
        log_warning "$(t 'log_package_cache_warnings')"
    fi
    
    # Entferne verwaiste Pakete (Orphans)
    orphans=$(pacman -Qtdq 2>/dev/null || true)
    if [[ -n "$orphans" ]]; then
        log_info "$(t 'log_removing_orphans')"
        sudo pacman -Rns $orphans --noconfirm 2>&1 | tee -a "$LOG_FILE" || log_warning "$(t 'log_orphans_removal_failed')"
    else
        log_info "$(t 'log_no_orphans')"
    fi
    
    # Flatpak-Cache bereinigen
    if command -v flatpak >/dev/null 2>&1; then
        log_info "$(t 'log_cleaning_flatpak_cache')"
        if flatpak uninstall --unused --noninteractive -y 2>&1 | tee -a "$LOG_FILE"; then
            log_success "$(t 'log_flatpak_cache_cleaned')"
        else
            log_warning "$(t 'log_flatpak_cache_warnings')"
        fi
    fi
    
    # Entferne verbleibende Cursor .deb Dateien im Script-Verzeichnis (falls vorhanden)
    if find "$SCRIPT_DIR" -maxdepth 1 -name "cursor*.deb" -type f 2>/dev/null | grep -q .; then
        log_info "$(t 'log_removing_cursor_deb')"
        find "$SCRIPT_DIR" -maxdepth 1 -name "cursor*.deb" -type f -delete 2>/dev/null || true
        log_success "$(t 'log_cursor_deb_removed')"
    fi
    
    # Entferne verbleibende AdGuard temporäre Dateien
    if find /tmp -maxdepth 1 -name "*adguard*" -o -name "*AdGuard*" -type d 2>/dev/null | grep -q .; then
        log_info "$(t 'log_removing_adguard_temp')"
        find /tmp -maxdepth 1 \( -name "*adguard*" -o -name "*AdGuard*" \) -type d -exec rm -rf {} + 2>/dev/null || true
        log_success "$(t 'log_adguard_temp_removed')"
    fi
    
    # Entferne verbleibende Cursor temporäre Verzeichnisse
    if find /tmp -maxdepth 1 -name "*cursor*" -type d 2>/dev/null | grep -q .; then
        log_info "$(t 'log_removing_cursor_temp')"
        find /tmp -maxdepth 1 -name "*cursor*" -type d -exec rm -rf {} + 2>/dev/null || true
        log_success "$(t 'log_cursor_temp_removed')"
    fi

    show_cleanup_result
fi

# ========== Zusammenfassung ==========
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

if [ "$DRY_RUN" = "true" ]; then
    show_dry_run_summary
else
    show_update_summary "$DURATION"

    log_success "$(t 'log_all_updates_completed')"

    # Statistiken speichern
    save_stats "$DURATION" "true"

    # Statistiken anzeigen (nur wenn interaktiv)
    if [ -t 0 ] && [ -t 1 ]; then
        show_stats
    fi

    if [ "$ENABLE_NOTIFICATIONS" = "true" ]; then
        notify-send "Update fertig!" "Dauer: ${MINUTES}m ${SECONDS}s" 2>/dev/null || true
    fi
fi

# ========== Script-Update-Check ==========
check_script_update() {
    if [ "$DRY_RUN" = "true" ]; then
        return 0
    fi
    
    log_info "$(t 'log_checking_script_updates')"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 $(t 'checking_script_version')"
    
    # Versuche zuerst Releases, dann Tags
    LATEST_VERSION=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/releases/latest" 2>/dev/null | grep -oP '"tag_name":\s*"v?\K[0-9.]+' | head -1 || echo "")
    
    # Falls kein Release, prüfe Tags direkt
    if [ -z "$LATEST_VERSION" ]; then
        LATEST_VERSION=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/git/refs/tags" 2>/dev/null | grep -oP '"ref":\s*"refs/tags/v?\K[0-9.]+' | sort -V | tail -1 || echo "")
    fi
    
    if [ -z "$LATEST_VERSION" ]; then
        log_warning "$(t 'log_could_not_fetch_version')"
        echo "⚠️  $(t 'version_check_failed')"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return 0
    fi
    
    # Entferne 'v' Präfix falls vorhanden
    LATEST_VERSION=$(echo "$LATEST_VERSION" | sed 's/^v//')
    
    # Versionsvergleich (Semantic Versioning wie WoltLab: Major.Minor.Patch)
    if [ "$LATEST_VERSION" != "$SCRIPT_VERSION" ]; then
        # Prüfe ob neue Version wirklich neuer ist (semantischer Vergleich)
        if printf '%s\n%s\n' "$SCRIPT_VERSION" "$LATEST_VERSION" | sort -V | head -1 | grep -q "^$SCRIPT_VERSION$"; then
            log_warning "$(t 'log_new_script_version') $SCRIPT_VERSION → $LATEST_VERSION"
            echo -e "${COLOR_WARNING}⚠️  $(t 'new_version_available') $SCRIPT_VERSION → $LATEST_VERSION${COLOR_RESET}"
            echo ""
            
            if [ "$ENABLE_AUTO_UPDATE" = "true" ]; then
                echo "   $(t 'auto_update_enabled')"
                read -p "   $(t 'update_script_now') " -n 1 -r
                echo ""
                if [[ $REPLY =~ ^[JjYy]$ ]]; then
                    log_info "$(t 'log_starting_auto_update')"
                    cd "$SCRIPT_DIR"
                    if git pull origin main 2>&1 | tee -a "$LOG_FILE"; then
                        log_success "$(t 'log_script_updated_success')"
                        echo -e "${COLOR_SUCCESS}✅ $(t 'script_updated_successfully')${COLOR_RESET}"
                        echo "   $(t 'please_rerun_script')"
                    else
                        log_error "$(t 'log_auto_update_failed')"
                        echo -e "${COLOR_ERROR}❌ $(t 'auto_update_failed')${COLOR_RESET}"
                        echo "   $(t 'please_update_manually')"
                    fi
                else
                    echo "   $(t 'update_skipped')"
                fi
            else
                echo "   $(t 'update_options')"
                echo "   1. Git: cd $(dirname "$SCRIPT_DIR")/cachyos-multi-updater && git pull"
                echo "   2. Download: https://github.com/$GITHUB_REPO/releases/latest"
                echo "   3. ZIP: https://github.com/$GITHUB_REPO/archive/refs/tags/v$LATEST_VERSION.zip"
                echo ""
                echo "   $(t 'tip_auto_update')"
            fi
        else
            log_info "Lokale Version ist neuer als GitHub-Version (Entwicklung?)"
            echo "ℹ️  $(t 'local_version') $SCRIPT_VERSION (GitHub: $LATEST_VERSION)"
        fi
    else
            log_info "$(t 'log_script_latest') $SCRIPT_VERSION)"
        echo "✅ $(t 'script_current') $SCRIPT_VERSION)"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

check_script_update

log_info "$(t 'log_script_update_completed')"

# Terminal offen halten (auch bei Desktop-Icon)
# WICHTIG: Bei Desktop-Icons ist Terminal oft nicht interaktiv
# Prüfe ob wir von einer Desktop-Datei gestartet wurden
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${COLOR_SUCCESS}✅ $(t 'all_updates_completed')${COLOR_RESET}"
echo ""
echo -e "${COLOR_INFO}➜ $(t 'press_enter_to_close')${COLOR_RESET}"
echo ""
# Immer warten - auch wenn nicht interaktiv (für Desktop-Icons)
if [ -t 0 ] && [ -t 1 ]; then
    # Interaktiv - normale Eingabe
    read -r </dev/tty 2>/dev/null || sleep 5
else
    # Nicht interaktiv (Desktop-Icon) - warte länger
    sleep 10
fi

