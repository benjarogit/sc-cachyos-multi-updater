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
readonly SCRIPT_VERSION="2.10.2"
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
MAX_LOG_FILES=10
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
                echo "WARNUNG: Ungültiger Wert für $key: '$value' (erwartet: true/false)" >&2
                return 1
            fi
            ;;
        MAX_LOG_FILES|DOWNLOAD_RETRIES)
            if [[ ! "$value" =~ ^[0-9]+$ ]]; then
                echo "WARNUNG: Ungültiger Wert für $key: '$value' (erwartet: Zahl)" >&2
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
                echo "  in Zeile $line_num von $CONFIG_FILE" >&2
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
    echo "Fehler: statistics.sh nicht gefunden in $SCRIPT_DIR/lib/" >&2
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
                echo "CachyOS Multi-Updater"
                echo "Version: $SCRIPT_VERSION"
                echo ""
                echo "Verwendung: $0 [OPTIONEN]"
                echo ""
                echo "Optionen:"
                echo "  --only-system        Nur System-Updates (CachyOS)"
                echo "  --only-aur           Nur AUR-Updates"
                echo "  --only-cursor        Nur Cursor-Update"
                echo "  --only-adguard       Nur AdGuard Home-Update"
                echo "  --only-flatpak       Nur Flatpak-Updates"
                echo "  --dry-run            Zeigt was gemacht würde, ohne Änderungen"
                echo "  --interactive, -i    Interaktiver Modus (wähle Updates aus)"
                echo "  --stats              Zeige Update-Statistiken"
                echo "  --version, -v        Zeigt die Versionsnummer"
                echo "  --help, -h           Zeigt diese Hilfe"
                echo ""
                exit 0
                ;;
            --version|-v)
                echo "CachyOS Multi-Updater Version $SCRIPT_VERSION"
                exit 0
                ;;
            *)
                echo "❌ Unbekannte Option: $1"
                echo "Verwende --help für Hilfe"
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
    echo "🔍 DRY-RUN MODUS: Es werden keine Änderungen vorgenommen!"
    echo ""
    echo "Geplante Updates:"
    [ "$UPDATE_SYSTEM" = "true" ] && echo "  ✅ System-Updates (CachyOS)"
    [ "$UPDATE_AUR" = "true" ] && echo "  ✅ AUR-Updates"
    [ "$UPDATE_CURSOR" = "true" ] && echo "  ✅ Cursor-Update"
    [ "$UPDATE_ADGUARD" = "true" ] && echo "  ✅ AdGuard Home-Update"
    [ "$UPDATE_FLATPAK" = "true" ] && echo "  ✅ Flatpak-Updates"
    echo ""
fi

# Farben sind bereits oben gesetzt (vor Module laden)

# ========== Update-Zeitplanung prüfen ==========
check_update_frequency() {
    local last_update_file
    last_update_file=$(find "$LOG_DIR" -name "update-*.log" -type f 2>/dev/null | sort -r | head -1)

    if [ -z "$last_update_file" ]; then
        log_info "Kein vorheriges Update gefunden - erstes Update"
        return 0
    fi

    local last_update_time
    last_update_time=$(stat -c %Y "$last_update_file" 2>/dev/null || echo 0)
    local current_time
    current_time=$(date +%s)
    local days_ago=$(( (current_time - last_update_time) / 86400 ))

    if [ $days_ago -gt 14 ]; then
        log_warning "Letztes Update vor $days_ago Tagen! Regelmäßige Updates (wöchentlich) empfohlen."
        echo ""
        echo "⚠️  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "   WARNUNG: Letztes Update vor $days_ago Tagen!"
        echo "   Regelmäßige Updates sind wichtig für Sicherheit und Stabilität."
        echo "   Empfehlung: Updates wöchentlich durchführen"
        echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    elif [ $days_ago -gt 7 ]; then
        log_info "Letztes Update vor $days_ago Tagen"
        echo "ℹ️  Letztes Update vor $days_ago Tagen"
    fi
}

# ========== Fehler-Report Generator ==========
generate_error_report() {
    local error_type="${1:-Unbekannt}"
    local error_file
    error_file="$LOG_DIR/error-report-$(date +%Y%m%d-%H%M%S).txt"

    {
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "FEHLER-REPORT: CachyOS Multi-Updater"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Fehlertyp:      $error_type"
        echo "Datum:          $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Script Version: $SCRIPT_VERSION"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "SYSTEM INFORMATION"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "OS:        $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2 || echo "Unbekannt")"
        echo "Kernel:    $(uname -r)"
        echo "User:      $(whoami)"
        echo "Hostname:  $(hostname)"
        echo "Disk:      $(df -h / 2>/dev/null | awk 'NR==2 {print $4 " free / " $2 " total"}' || echo "N/A")"
        echo "Memory:    $(free -h 2>/dev/null | awk 'NR==2 {print $7 " available / " $2 " total"}' || echo "N/A")"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "LETZTE 50 LOG-ZEILEN"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        tail -50 "$LOG_FILE" 2>/dev/null || echo "Log-Datei nicht verfügbar"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "KONFIGURATION"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        if [ -f "$CONFIG_FILE" ]; then
            cat "$CONFIG_FILE"
        else
            echo "Keine Config-Datei vorhanden (Standard-Einstellungen)"
        fi
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "ENDE FEHLER-REPORT"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    } > "$error_file"

    log_error "Fehler-Report erstellt: $error_file"
    echo ""
    echo "❌ Ein Fehler ist aufgetreten!"
    echo "   Fehler-Report erstellt: $error_file"
    echo "   Bitte prüfe den Report für Details."
    echo ""
}

# ========== System-Info sammeln ==========
collect_system_info() {
    cat >> "$LOG_FILE" <<EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SYSTEM INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OS:             $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2 || echo "Unbekannt")
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
        log_error "Script wurde mit Fehler beendet (Exit-Code: $exit_code)"
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
            log_warning "Download fehlgeschlagen, Versuch $retry/$max_retries..."
            sleep 2
        else
            log_error "Download nach $max_retries Versuchen fehlgeschlagen!"
            return 1
        fi
    done
}

# ========== Alte Logs aufräumen ==========
cleanup_old_logs() {
    if [ -d "$LOG_DIR" ]; then
        find "$LOG_DIR" -name "update-*.log" -type f | sort -r | tail -n +$((MAX_LOG_FILES + 1)) | xargs rm -f 2>/dev/null || true
    fi
}

cleanup_old_logs

# System-Info sammeln
collect_system_info

log_info "CachyOS Multi-Updater Version $SCRIPT_VERSION"
log_info "Update gestartet..."
log_info "Log-Datei: $LOG_FILE"
[ "$DRY_RUN" = "true" ] && log_info "DRY-RUN Modus aktiviert"
[ "$ENABLE_COLORS" = "true" ] && log_info "Farbige Ausgabe aktiviert"

# Prüfe Update-Häufigkeit
check_update_frequency

# Geschätzte Dauer anzeigen
estimate_duration

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${COLOR_BOLD}CachyOS Multi-Updater v$SCRIPT_VERSION${COLOR_RESET}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Passwort-Abfrage VOR den Updates (damit Desktop-Icon funktioniert)
if [ "$DRY_RUN" != "true" ]; then
    echo -e "${COLOR_INFO}🔐 $(t 'sudo_required')${COLOR_RESET}"
    echo ""
    sudo -v || {
        log_error "Sudo authentication failed"
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

# ========== CachyOS updaten ==========
if [ "$UPDATE_SYSTEM" = "true" ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'system_updates')" "🔄"

    log_info "Starte CachyOS-Update..."
    show_system_update_start

    if [ "$DRY_RUN" = "true" ]; then
        packages_available=$(pacman -Qu 2>/dev/null | wc -l || echo "0")
        log_info "[DRY-RUN] Verfügbare Updates: $packages_available Pakete"
        log_info "[DRY-RUN] Würde ausführen: sudo pacman -Syu --noconfirm"
    else
        # Zähle Pakete VOR dem Update
        SYSTEM_PACKAGES=$(pacman -Qu 2>/dev/null | wc -l || echo "0")
        # Bereinige Newlines und Whitespace
        SYSTEM_PACKAGES=$(echo "$SYSTEM_PACKAGES" | tr -d '\n\r' | xargs)
        log_info "Zu aktualisierende Pakete: $SYSTEM_PACKAGES"

        # Führe Pacman-Update durch
        if sudo pacman -Syu --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
            SYSTEM_UPDATED=true
            log_success "CachyOS-Update erfolgreich ($SYSTEM_PACKAGES Pakete aktualisiert)"
            show_system_update_result "$SYSTEM_PACKAGES"
            show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'system_updates')" "✅"
        else
            log_error "Pacman-Update fehlgeschlagen!"
            show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'system_updates')" "❌"
            exit $EXIT_UPDATE_ERROR
        fi
    fi
else
    log_info "System-Update übersprungen (deaktiviert)"
fi

# ========== AUR updaten ==========
if [ "$UPDATE_AUR" = "true" ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'aur_updates')" "🔄"

    log_info "Starte AUR-Update..."
    show_aur_update_start

    if [ "$DRY_RUN" = "true" ]; then
        if command -v yay >/dev/null 2>&1; then
            log_info "[DRY-RUN] Würde ausführen: yay -Syu --noconfirm"
        elif command -v paru >/dev/null 2>&1; then
            log_info "[DRY-RUN] Würde ausführen: paru -Syu --noconfirm"
        else
            log_warning "[DRY-RUN] Kein AUR-Helper gefunden"
        fi
    else
        if command -v yay >/dev/null 2>&1; then
            log_info "Verwende yay als AUR-Helper"
            AUR_PACKAGES=$(yay -Qua 2>/dev/null | wc -l || echo "0")
            if yay -Syu --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
                AUR_UPDATED=true
                log_success "AUR-Update mit yay erfolgreich"
                show_aur_update_result "$AUR_PACKAGES"
                show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'aur_updates')" "✅"
            else
                log_warning "AUR-Update mit yay hatte Warnungen"
                show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'aur_updates')" "⚠️"
            fi
        elif command -v paru >/dev/null 2>&1; then
            log_info "Verwende paru als AUR-Helper"
            AUR_PACKAGES=$(paru -Qua 2>/dev/null | wc -l || echo "0")
            if paru -Syu --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
                AUR_UPDATED=true
                log_success "AUR-Update mit paru erfolgreich"
                show_aur_update_result "$AUR_PACKAGES"
                show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'aur_updates')" "✅"
            else
                log_warning "AUR-Update mit paru hatte Warnungen"
                show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'aur_updates')" "⚠️"
            fi
        else
            log_warning "Kein AUR-Helper (yay/paru) gefunden – überspringe AUR."
            show_component_not_found "yay/paru"
            show_progress $CURRENT_STEP $TOTAL_STEPS "$(t 'aur_updates')" "⏭️"
        fi
    fi
else
    log_info "AUR-Update übersprungen (deaktiviert)"
fi

# ========== Cursor updaten ==========
if [ "$UPDATE_CURSOR" = "true" ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "🔄"

    log_info "Starte Cursor-Update..."
    show_cursor_update_start
    
    if [ "$DRY_RUN" = "true" ]; then
        if command -v cursor >/dev/null 2>&1; then
            # Versuche package.json zu finden (ohne cursor --version aufzurufen!)
            CURSOR_PATH=$(which cursor)
            CURSOR_INSTALL_DIR=$(dirname "$(readlink -f "$CURSOR_PATH")")
            CURRENT_VERSION="unbekannt"
            if [ -f "$CURSOR_INSTALL_DIR/resources/app/package.json" ]; then
                CURRENT_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$CURSOR_INSTALL_DIR/resources/app/package.json" 2>/dev/null | head -1 || echo "unbekannt")
            fi
            log_info "[DRY-RUN] Aktuelle Cursor-Version: $CURRENT_VERSION"
            log_info "[DRY-RUN] Würde Cursor herunterladen und aktualisieren"
        else
            log_warning "[DRY-RUN] Cursor nicht gefunden"
        fi
    elif ! command -v cursor >/dev/null 2>&1; then
        log_warning "Cursor nicht gefunden – bitte manuell installieren!"
        show_component_not_found "Cursor"
    else
        # Prüfe, ob Cursor über pacman/AUR installiert ist
        if pacman -Q cursor 2>/dev/null | grep -q cursor; then
            CURSOR_PACMAN_VERSION=$(pacman -Q cursor | awk '{print $2}')
            log_info "Cursor ist über pacman installiert (Version: $CURSOR_PACMAN_VERSION)"
            show_cursor_pacman_managed "$CURSOR_PACMAN_VERSION"
            log_info "Cursor-Update übersprungen (wird über pacman verwaltet)"
            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "⏭️"
        elif pacman -Q cursor-bin 2>/dev/null | grep -q cursor-bin; then
            CURSOR_AUR_VERSION=$(pacman -Q cursor-bin | awk '{print $2}')
            log_info "Cursor ist über AUR installiert (Version: $CURSOR_AUR_VERSION)"
            show_cursor_pacman_managed "$CURSOR_AUR_VERSION"
            log_info "Cursor-Update übersprungen (wird über AUR verwaltet)"
            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "⏭️"
        else
            # Cursor-Pfad finden
            CURSOR_PATH=$(which cursor)
            CURSOR_INSTALL_DIR=$(dirname "$(readlink -f "$CURSOR_PATH")")

            log_info "Cursor gefunden in: $CURSOR_INSTALL_DIR"

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
            log_info "Aktuelle Cursor-Version: $CURRENT_VERSION"
            
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
                log_info "Cursor-Version erkannt: $CURRENT_VERSION"
                
                # NEU: Versuche Version OHNE Download zu prüfen (HTTP HEAD Request)
                # Die API gibt einen Redirect mit Version im Dateinamen zurück
                log_info "Prüfe verfügbare Version via HTTP HEAD..."
                LOCATION_HEADER=$(curl -sI "$DOWNLOAD_URL" 2>/dev/null | grep -i "^location:" | cut -d' ' -f2- | tr -d '\r\n' || echo "")
                
                if [ -n "$LOCATION_HEADER" ]; then
                    # Extrahiere Version aus Dateinamen: cursor_2.0.69_amd64.deb -> 2.0.69
                    LATEST_VERSION=$(echo "$LOCATION_HEADER" | grep -oP 'cursor_(\K[0-9.]+)' | head -1 || echo "")

                    if [ -n "$LATEST_VERSION" ]; then
                        log_info "Neueste verfügbare Version (via HTTP HEAD): $LATEST_VERSION"

                        # Vergleiche Versionen
                        if [ "$CURRENT_VERSION" = "$LATEST_VERSION" ]; then
                            SKIP_INSTALL=true
                            log_info "Cursor ist bereits auf neuester Version ($CURRENT_VERSION)"
                            show_cursor_update_result "$CURRENT_VERSION" "$CURRENT_VERSION"
                            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "✅"
                        else
                            log_info "Update verfügbar: $CURRENT_VERSION → $LATEST_VERSION"
                            show_cursor_update_downloading "$LATEST_VERSION"
                            # Download wird jetzt durchgeführt
                            log_info "Lade Cursor .deb von: $DOWNLOAD_URL"
                            
                            if download_with_retry "$DOWNLOAD_URL" "$DEB_FILE"; then
                                if [[ -f "$DEB_FILE" ]] && [[ $(stat -c%s "$DEB_FILE") -gt 50000000 ]]; then
                                    DEB_SIZE=$(du -h "$DEB_FILE" | cut -f1)
                                    log_success "Download erfolgreich: $DEB_SIZE"
                                else
                                    log_error "Download zu klein oder fehlgeschlagen!"
                                    rm -f "$DEB_FILE"
                                    SKIP_INSTALL=true
                                    show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "❌"
                                fi
                            else
                                log_error "Cursor-Download fehlgeschlagen!"
                                rm -f "$DEB_FILE"
                                SKIP_INSTALL=true
                                show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "❌"
                            fi
                        fi
                    else
                        log_warning "Version konnte nicht aus Location-Header extrahiert werden, fahre mit Download fort..."
                        echo "⬇️  Lade Cursor .deb für Versionsprüfung..."
                        
                        if download_with_retry "$DOWNLOAD_URL" "$DEB_FILE"; then
                            if [[ -f "$DEB_FILE" ]] && [[ $(stat -c%s "$DEB_FILE") -gt 50000000 ]]; then
                                DEB_SIZE=$(du -h "$DEB_FILE" | cut -f1)
                                log_success "Download erfolgreich: $DEB_SIZE"
                                echo "✅ Download erfolgreich: $DEB_SIZE"
                                
                                # Extrahiere Version aus .deb (Fallback-Methode)
                                TEMP_EXTRACT_DIR=$(mktemp -d -t cursor-version-check.XXXXXXXXXX)
                                if ! cd "$TEMP_EXTRACT_DIR" 2>/dev/null; then
                                    log_warning "Konnte nicht in temporäres Verzeichnis wechseln, fahre mit Installation fort..."
                                    rm -rf "$TEMP_EXTRACT_DIR"
                                elif ! ar x "$DEB_FILE" 2>/dev/null; then
                                    cd "$SCRIPT_DIR" || true
                                    rm -rf "$TEMP_EXTRACT_DIR"
                                    log_warning "Fehler beim Extrahieren der .deb-Datei, fahre mit Installation fort..."
                                else
                                    # Finde die tar-Datei (kann .gz, .xz, .bz2 oder unkomprimiert sein)
                                    TAR_FILE=$(ls data.tar.* 2>/dev/null | head -1)
                                    if [ -z "$TAR_FILE" ]; then
                                        cd "$SCRIPT_DIR" || true
                                        rm -rf "$TEMP_EXTRACT_DIR"
                                        log_warning "Keine data.tar.* Datei gefunden, fahre mit Installation fort..."
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
                                                    log_info "Neueste verfügbare Version (aus .deb): $LATEST_VERSION"
                                                    echo "📌 Verfügbare Version: $LATEST_VERSION"
                                                    
                                                    # Vergleiche Versionen
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
                    log_warning "HTTP HEAD Request fehlgeschlagen, fahre mit Download fort..."
                    echo "⬇️  Lade Cursor .deb für Versionsprüfung..."
                    
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
                log_warning "Cursor-Version konnte nicht ermittelt werden, fahre mit Update fort..."
                echo "⬇️  Lade Cursor .deb..."
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
                log_info "Cursor-Update übersprungen (bereits aktuell)"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                echo ""
            else
                # .deb wurde bereits heruntergeladen, fahre mit Installation fort
                if [[ -f "$DEB_FILE" ]] && [[ $(stat -c%s "$DEB_FILE") -gt 50000000 ]]; then
                    # Cursor-Prozesse prüfen (nicht automatisch schließen)
                    # Verwende -x für exact match, verhindert false positives
                    cursor_pids=$(pgrep -x "cursor" 2>/dev/null || pgrep -x "Cursor" 2>/dev/null || true)
                    if [ -n "$cursor_pids" ]; then
                        log_warning "Cursor läuft noch (PID: $cursor_pids) - bitte manuell schließen für sauberes Update"
                        echo "⚠️  Cursor läuft noch (PID: $cursor_pids)"
                        echo "   Bitte manuell schließen für sauberes Update"
                        echo "   (Cursor wird nicht automatisch geschlossen)"
                    else
                        log_info "Keine laufenden Cursor-Prozesse gefunden"
                        echo "ℹ️  Cursor läuft nicht"
                    fi
                    
                    # Extrahiere .deb
                    extract_dir=$(mktemp -d -t cursor-extract.XXXXXXXXXX)
                    trap 'rm -rf "$extract_dir" "$DEB_FILE"' EXIT

                    log_info "Extrahiere Cursor .deb..."
                    show_cursor_update_installing
                    cd "$extract_dir"

                    if ! ar x "$DEB_FILE" 2>&1 | tee -a "$LOG_FILE"; then
                        log_error "Fehler beim Extrahieren des .deb-Archivs"
                        echo "❌ Fehler beim Extrahieren!"
                        rm -rf "$extract_dir" "$DEB_FILE"
                        exit $EXIT_DOWNLOAD_ERROR
                    elif ! tar -xf data.tar.* 2>&1 | tee -a "$LOG_FILE"; then
                        log_error "Fehler beim Extrahieren der Daten"
                        echo "❌ Fehler beim Extrahieren der Daten!"
                        rm -rf "$extract_dir" "$DEB_FILE"
                        exit $EXIT_DOWNLOAD_ERROR
                    else
                        # Finde Cursor-Binary und Ressourcen
                        install_success=false

                        if [[ -d "opt/Cursor" ]]; then
                            log_info "Installiere Cursor-Update (opt/Cursor)..."
                            show_cursor_update_installing
                            if sudo cp -rf opt/Cursor/* "$CURSOR_INSTALL_DIR/" 2>&1 | tee -a "$LOG_FILE"; then
                                sudo chmod +x "$CURSOR_INSTALL_DIR/cursor" 2>/dev/null || true
                                log_success "Cursor-Update installiert"
                                install_success=true
                            elif sudo cp -rf opt/Cursor/* "$(dirname "$CURSOR_INSTALL_DIR")/" 2>&1 | tee -a "$LOG_FILE"; then
                                sudo chmod +x "$(dirname "$CURSOR_INSTALL_DIR")/cursor" 2>/dev/null || true
                                log_success "Cursor-Update installiert (alternativer Pfad)"
                                install_success=true
                            elif sudo cp -rf opt/Cursor /opt/ 2>&1 | tee -a "$LOG_FILE"; then
                                sudo chmod +x /opt/Cursor/cursor 2>/dev/null || true
                                log_success "Cursor-Update installiert (nach /opt)"
                                install_success=true
                            fi
                        elif [[ -d "usr/share/cursor" ]]; then
                            log_info "Installiere Cursor-Update (usr/share/cursor)..."
                            show_cursor_update_installing
                            if sudo cp -rf usr/share/cursor/* "$CURSOR_INSTALL_DIR/" 2>&1 | tee -a "$LOG_FILE"; then
                                sudo chmod +x "$CURSOR_INSTALL_DIR/cursor" 2>/dev/null || true
                                log_success "Cursor-Update installiert"
                                install_success=true
                            fi
                        fi

                        # Cleanup IMMER durchführen (trap entfernen vor cleanup)
                        trap - EXIT
                        log_info "Bereinige temporäre Dateien..."
                        rm -rf "$extract_dir" "$DEB_FILE"
                        log_info "Temporäre Dateien gelöscht"

                        if [ "$install_success" = "true" ]; then
                            # Neue Version prüfen (nur package.json - --version öffnet Cursor!)
                            sleep 1
                            NEW_VERSION="installiert"
                            if [ -f "$CURSOR_INSTALL_DIR/resources/app/package.json" ]; then
                                NEW_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$CURSOR_INSTALL_DIR/resources/app/package.json" 2>/dev/null | head -1 || echo "installiert")
                            fi
                            CURSOR_UPDATED=true
                            log_success "Cursor updated: $CURRENT_VERSION → $NEW_VERSION"
                            show_cursor_update_result "$CURRENT_VERSION" "$NEW_VERSION"
                            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "✅"
                        else
                            log_error "Cursor-Dateien nicht gefunden im .deb oder Installation fehlgeschlagen!"
                            show_progress $CURRENT_STEP $TOTAL_STEPS "Cursor Editor Update" "❌"
                        fi
                    fi
                    # WICHTIG: cd zurück zum Script-Verzeichnis
                    cd "$SCRIPT_DIR" || true
                else
                    log_error "Download zu klein oder fehlgeschlagen!"
                    echo "❌ Download zu klein oder fehlgeschlagen!"
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

    log_info "Starte AdGuardHome-Update..."
    show_adguard_update_start
    agh_dir="$HOME/AdGuardHome"
    temp_dir=$(mktemp -d -t adguard-update.XXXXXXXXXX)
    trap 'rm -rf "$temp_dir"' EXIT
    
    if [ "$DRY_RUN" = "true" ]; then
        if [[ -f "$agh_dir/AdGuardHome" ]]; then
            current_version=$(cd "$agh_dir" && ./AdGuardHome --version 2>/dev/null | grep -oP 'v\K[0-9.]+' || echo "0.0.0")
            log_info "[DRY-RUN] Aktuelle AdGuard-Version: v$current_version"
            log_info "[DRY-RUN] Würde AdGuard Home aktualisieren"
        else
            log_warning "[DRY-RUN] AdGuard Home nicht gefunden in $agh_dir"
        fi
    elif [[ -f "$agh_dir/AdGuardHome" ]]; then
        cd "$agh_dir"
        
        log_info "Stoppe AdGuardHome-Service..."
        systemctl --user stop AdGuardHome 2>&1 | tee -a "$LOG_FILE" || log_warning "AdGuardHome-Service konnte nicht gestoppt werden"

        current_version=$(./AdGuardHome --version 2>/dev/null | grep -oP 'v\K[0-9.]+' || echo "0.0.0")
        log_info "Aktuelle AdGuard-Version: v$current_version"

        # Prüfe neueste Version über GitHub Releases API
        log_info "Prüfe verfügbare AdGuard Home-Version..."
        latest_version_gh=$(curl -s "https://api.github.com/repos/AdguardTeam/AdGuardHome/releases/latest" 2>/dev/null | grep -oP '"tag_name":\s*"v\K[0-9.]+' | head -1 || echo "")

        # Entferne 'v' Präfix falls vorhanden
        if [ -n "$latest_version_gh" ]; then
            latest_version_gh=$(echo "$latest_version_gh" | sed 's/^v//')
            log_info "Neueste verfügbare Version (GitHub): v$latest_version_gh"

            # Versionsvergleich - wenn bereits aktuell, überspringe Download
            if [ "$current_version" = "$latest_version_gh" ]; then
                log_info "AdGuardHome ist bereits auf neuester Version (v$current_version)"
                show_adguard_update_result "$current_version" "$current_version"
                ADGUARD_UPDATED=false
                show_progress $CURRENT_STEP $TOTAL_STEPS "AdGuard Home Update" "✅"
            else
                log_info "Update verfügbar: v$current_version → v$latest_version_gh"
                show_adguard_update_downloading "$latest_version_gh"
                
                backup_dir="$agh_dir-backup-$(date +%Y%m%d-%H%M%S)"
                mkdir -p "$backup_dir"
                cp AdGuardHome.yaml data/* "$backup_dir/" 2>/dev/null || log_warning "Backup konnte nicht erstellt werden"
                log_info "Backup erstellt in: $backup_dir"

                # Offizieller Download-Link von AdGuard (siehe https://adguard-dns.io/kb/de/adguard-home/getting-started/)
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
                                        echo "✅ AdGuardHome updated: v$current_version → v$new_version"
                                    else
                                        log_error "Fehler beim Kopieren der neuen AdGuardHome-Binary"
                                    fi
                                else
                                    log_info "AdGuardHome ist bereits aktuell (v$new_version)"
                                    echo "ℹ️ AdGuardHome ist aktuell (v$new_version)."
                                fi
                            else
                                log_error "AdGuardHome-Binary nicht im Archiv gefunden"
                            fi
                        else
                            log_error "Fehler beim Extrahieren von AdGuardHome"
                        fi
                    else
                        log_error "AdGuardHome-Download fehlgeschlagen!"
                    fi
                else
                    log_error "AdGuardHome-Download fehlgeschlagen!"
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
                    log_error "AdGuardHome-Download fehlgeschlagen!"
                fi
            else
                log_error "AdGuardHome-Download fehlgeschlagen!"
            fi
        fi
        rm -rf "$temp_dir"

        log_info "Starte AdGuardHome-Service..."
        if systemctl --user start AdGuardHome 2>&1 | tee -a "$LOG_FILE"; then
            sleep 2
            if systemctl --user is-active --quiet AdGuardHome; then
                log_success "AdGuardHome-Service läuft erfolgreich"
            else
                log_warning "AdGuardHome-Service gestartet, aber Status unklar"
            fi
        else
            log_warning "AdGuardHome-Service konnte nicht gestartet werden"
        fi
    else
        log_warning "AdGuardHome Binary nicht gefunden in: $agh_dir"
        echo "⚠️ AdGuardHome Binary nicht gefunden in: $agh_dir"
    fi
else
    log_info "AdGuard Home-Update übersprungen (deaktiviert)"
fi

# ========== Flatpak updaten ==========
if [ "$UPDATE_FLATPAK" = "true" ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress $CURRENT_STEP $TOTAL_STEPS "Flatpak-Updates" "🔄"

    log_info "Starte Flatpak-Update..."
    show_flatpak_update_start
    
    if [ "$DRY_RUN" = "true" ]; then
        if command -v flatpak >/dev/null 2>&1; then
            log_info "[DRY-RUN] Würde ausführen: flatpak update --noninteractive -y"
            FLATPAK_PACKAGES=$(flatpak remote-ls --updates 2>/dev/null | wc -l || echo "0")
            log_info "[DRY-RUN] Verfügbare Flatpak-Updates: $FLATPAK_PACKAGES Pakete"
        else
            log_warning "[DRY-RUN] Flatpak nicht gefunden"
        fi
    else
        if command -v flatpak >/dev/null 2>&1; then
            # Prüfe verfügbare Updates
            FLATPAK_UPDATES=$(flatpak remote-ls --updates 2>/dev/null | wc -l || echo "0")
            FLATPAK_UPDATES=$(echo "$FLATPAK_UPDATES" | tr -d '\n\r' | xargs)
            log_info "Verfügbare Flatpak-Updates: $FLATPAK_UPDATES Pakete"


            if [ "$FLATPAK_UPDATES" -gt 0 ] 2>/dev/null; then
                # Verwende --noninteractive für vollständig automatische Updates
                if flatpak update --noninteractive -y 2>&1 | grep -E "^(Installing |Updating |Removing )" | tee -a "$LOG_FILE"; then
                    FLATPAK_UPDATED=true
                    FLATPAK_PACKAGES="$FLATPAK_UPDATES"
                    log_success "Flatpak-Update erfolgreich ($FLATPAK_UPDATES Pakete aktualisiert)"
                    show_flatpak_update_result "$FLATPAK_UPDATES"
                    show_progress $CURRENT_STEP $TOTAL_STEPS "Flatpak-Updates" "✅"
                else
                    log_warning "Flatpak-Update hatte Warnungen"
                    show_progress $CURRENT_STEP $TOTAL_STEPS "Flatpak-Updates" "⚠️"
                fi
            else
                log_info "Keine Flatpak-Updates verfügbar"
                show_flatpak_update_result 0
                FLATPAK_PACKAGES=0
                show_progress $CURRENT_STEP $TOTAL_STEPS "Flatpak-Updates" "✅"
            fi
        else
            log_warning "Flatpak nicht gefunden – überspringe Flatpak-Updates."
            show_component_not_found "Flatpak"
            show_progress $CURRENT_STEP $TOTAL_STEPS "Flatpak-Updates" "⏭️"
        fi
    fi
else
    log_info "Flatpak-Update übersprungen (deaktiviert)"
fi

# ========== Cleanup ==========
if [ "$DRY_RUN" = "true" ]; then
    log_info "[DRY-RUN] Würde System-Cleanup durchführen"
    log_info "[DRY-RUN] Würde ausführen: paccache -rk3"
    log_info "[DRY-RUN] Würde ausführen: sudo pacman -Sc --noconfirm"
    log_info "[DRY-RUN] Würde ausführen: flatpak uninstall --unused --noninteractive -y"
    log_info "[DRY-RUN] Würde verbleibende .deb Dateien und temporäre Verzeichnisse entfernen"
else
    log_info "Starte System-Cleanup..."
    show_cleanup_start
    
    # Alte Paketversionen im Cache behalten (nur die letzten 3 Versionen)
    log_info "Bereinige Paket-Cache (behält letzte 3 Versionen)..."
    paccache -rk3 2>&1 | tee -a "$LOG_FILE" || log_warning "Paccache fehlgeschlagen"
    
    # Entferne alte/deinstallierte Pakete aus dem Cache
    log_info "Entferne alte und deinstallierte Pakete aus dem Cache..."
    if yes | sudo pacman -Sc --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Paket-Cache bereinigt"
    else
        log_warning "Paket-Cache-Bereinigung hatte Warnungen"
    fi
    
    # Entferne verwaiste Pakete (Orphans)
    orphans=$(pacman -Qtdq 2>/dev/null || true)
    if [[ -n "$orphans" ]]; then
        log_info "Entferne verwaiste Pakete..."
        sudo pacman -Rns $orphans --noconfirm 2>&1 | tee -a "$LOG_FILE" || log_warning "Orphan-Pakete konnten nicht entfernt werden"
    else
        log_info "Keine Orphan-Pakete gefunden"
    fi
    
    # Flatpak-Cache bereinigen
    if command -v flatpak >/dev/null 2>&1; then
        log_info "Bereinige Flatpak-Cache..."
        if flatpak uninstall --unused --noninteractive -y 2>&1 | tee -a "$LOG_FILE"; then
            log_success "Flatpak-Cache bereinigt"
        else
            log_warning "Flatpak-Cache-Bereinigung hatte Warnungen (oder nichts zu bereinigen)"
        fi
    fi
    
    # Entferne verbleibende Cursor .deb Dateien im Script-Verzeichnis (falls vorhanden)
    if find "$SCRIPT_DIR" -maxdepth 1 -name "cursor*.deb" -type f 2>/dev/null | grep -q .; then
        log_info "Entferne verbleibende Cursor .deb Dateien..."
        find "$SCRIPT_DIR" -maxdepth 1 -name "cursor*.deb" -type f -delete 2>/dev/null || true
        log_success "Cursor .deb Dateien entfernt"
    fi
    
    # Entferne verbleibende AdGuard temporäre Dateien
    if find /tmp -maxdepth 1 -name "*adguard*" -o -name "*AdGuard*" -type d 2>/dev/null | grep -q .; then
        log_info "Entferne verbleibende AdGuard temporäre Dateien..."
        find /tmp -maxdepth 1 \( -name "*adguard*" -o -name "*AdGuard*" \) -type d -exec rm -rf {} + 2>/dev/null || true
        log_success "AdGuard temporäre Dateien entfernt"
    fi
    
    # Entferne verbleibende Cursor temporäre Verzeichnisse
    if find /tmp -maxdepth 1 -name "*cursor*" -type d 2>/dev/null | grep -q .; then
        log_info "Entferne verbleibende Cursor temporäre Verzeichnisse..."
        find /tmp -maxdepth 1 -name "*cursor*" -type d -exec rm -rf {} + 2>/dev/null || true
        log_success "Cursor temporäre Verzeichnisse entfernt"
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

    log_success "Alle Updates abgeschlossen!"

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
    
    log_info "Prüfe auf Script-Updates..."
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 Script-Version prüfen..."
    
    # Versuche zuerst Releases, dann Tags
    LATEST_VERSION=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/releases/latest" 2>/dev/null | grep -oP '"tag_name":\s*"v?\K[0-9.]+' | head -1 || echo "")
    
    # Falls kein Release, prüfe Tags direkt
    if [ -z "$LATEST_VERSION" ]; then
        LATEST_VERSION=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/git/refs/tags" 2>/dev/null | grep -oP '"ref":\s*"refs/tags/v?\K[0-9.]+' | sort -V | tail -1 || echo "")
    fi
    
    if [ -z "$LATEST_VERSION" ]; then
        log_warning "Konnte neueste Version nicht abrufen"
        echo "⚠️  Versionsprüfung fehlgeschlagen (keine Internetverbindung?)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return 0
    fi
    
    # Entferne 'v' Präfix falls vorhanden
    LATEST_VERSION=$(echo "$LATEST_VERSION" | sed 's/^v//')
    
    # Versionsvergleich (Semantic Versioning wie WoltLab: Major.Minor.Patch)
    if [ "$LATEST_VERSION" != "$SCRIPT_VERSION" ]; then
        # Prüfe ob neue Version wirklich neuer ist (semantischer Vergleich)
        if printf '%s\n%s\n' "$SCRIPT_VERSION" "$LATEST_VERSION" | sort -V | head -1 | grep -q "^$SCRIPT_VERSION$"; then
            log_warning "Neue Script-Version verfügbar: $SCRIPT_VERSION → $LATEST_VERSION"
            echo -e "${COLOR_WARNING}⚠️  Neue Script-Version verfügbar: $SCRIPT_VERSION → $LATEST_VERSION${COLOR_RESET}"
            echo ""
            
            if [ "$ENABLE_AUTO_UPDATE" = "true" ]; then
                echo "   Automatisches Update ist aktiviert."
                read -p "   Script jetzt aktualisieren? (j/N): " -n 1 -r
                echo ""
                if [[ $REPLY =~ ^[JjYy]$ ]]; then
                    log_info "Starte automatisches Script-Update..."
                    cd "$SCRIPT_DIR"
                    if git pull origin main 2>&1 | tee -a "$LOG_FILE"; then
                        log_success "Script erfolgreich aktualisiert!"
                        echo -e "${COLOR_SUCCESS}✅ Script erfolgreich aktualisiert!${COLOR_RESET}"
                        echo "   Bitte Script erneut ausführen, um die neue Version zu verwenden."
                    else
                        log_error "Automatisches Update fehlgeschlagen!"
                        echo -e "${COLOR_ERROR}❌ Automatisches Update fehlgeschlagen!${COLOR_RESET}"
                        echo "   Bitte manuell aktualisieren."
                    fi
                else
                    echo "   Update übersprungen."
                fi
            else
                echo "   Update-Optionen:"
                echo "   1. Git: cd $(dirname "$SCRIPT_DIR")/cachyos-multi-updater && git pull"
                echo "   2. Download: https://github.com/$GITHUB_REPO/releases/latest"
                echo "   3. ZIP: https://github.com/$GITHUB_REPO/archive/refs/tags/v$LATEST_VERSION.zip"
                echo ""
                echo "   Tipp: Setze ENABLE_AUTO_UPDATE=true in config.conf für automatische Updates"
            fi
        else
            log_info "Lokale Version ist neuer als GitHub-Version (Entwicklung?)"
            echo "ℹ️  Lokale Version: $SCRIPT_VERSION (GitHub: $LATEST_VERSION)"
        fi
    else
        log_info "Script ist auf dem neuesten Stand (Version $SCRIPT_VERSION)"
        echo "✅ Script ist aktuell (Version $SCRIPT_VERSION)"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

check_script_update

log_info "Update-Script erfolgreich beendet"

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

