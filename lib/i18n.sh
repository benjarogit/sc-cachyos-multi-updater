#!/bin/bash
#
# CachyOS Multi-Updater - Internationalization Module
# Automatic language detection and translation support
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)
#
# This is free and open source software (FOSS).
# You are welcome to modify and distribute it under the terms of the MIT License.
#
# Repository: https://github.com/SunnyCueq/cachyos-multi-updater
#

# ========== Language Detection ==========
detect_language() {
    # Prüfe LANG und LC_ALL Umgebungsvariablen
    local lang="${LANG:-${LC_ALL:-en_US.UTF-8}}"

    # Extrahiere Sprachcode (z.B. de aus de_DE.UTF-8)
    lang="${lang%%_*}"
    lang="${lang%%.*}"

    case "$lang" in
        de|DE)
            echo "de"
            ;;
        *)
            echo "en"
            ;;
    esac
}

# Automatische Spracherkennung
DETECTED_LANG=$(detect_language)

# ========== Translation Function ==========
# Verwendung: t "key"
t() {
    local key="$1"

    case "$DETECTED_LANG" in
        de)
            case "$key" in
                # Allgemein
                "press_enter_to_close") echo "Drücke Enter um das Fenster zu schließen" ;;
                "all_updates_completed") echo "Alle Updates wurden erfolgreich abgeschlossen!" ;;
                "sudo_required") echo "Sudo-Passwort wird benötigt..." ;;
                "sudo_failed") echo "Sudo-Authentifizierung fehlgeschlagen!" ;;
                "checking_updates") echo "VERFÜGBARE UPDATES WERDEN GEPRÜFT..." ;;
                "update_process_starts") echo "UPDATE-VORGANG STARTET" ;;
                "update_summary") echo "UPDATE ABGESCHLOSSEN" ;;
                "completed") echo "abgeschlossen" ;;

                # Komponenten
                "system_update") echo "System-Update" ;;
                "system_updates") echo "System-Updates (pacman)" ;;
                "aur_update") echo "AUR-Update" ;;
                "aur_updates") echo "AUR-Updates (yay/paru)" ;;
                "cursor_editor_update") echo "Cursor Editor Update" ;;
                "adguard_home_update") echo "AdGuard Home Update" ;;
                "flatpak_updates") echo "Flatpak-Updates" ;;

                # Status-Texte
                "running") echo "läuft..." ;;
                "checking") echo "wird geprüft..." ;;
                "downloading") echo "Lade" ;;
                "installing") echo "Installiere Update..." ;;
                "already_uptodate") echo "Bereits aktuell" ;;
                "packages_available") echo "Pakete verfügbar" ;;
                "packages_updated") echo "Pakete aktualisiert" ;;
                "package") echo "Paket" ;;
                "packages") echo "Pakete" ;;
                "update_available") echo "Update verfügbar" ;;
                "updated") echo "Aktualisiert" ;;
                "not_installed") echo "nicht installiert" ;;
                "skipped") echo "übersprungen" ;;
                "managed_by_pacman") echo "Über pacman verwaltet" ;;

                # Cleanup
                "cleanup") echo "Cleanup..." ;;
                "system_cleaned") echo "System bereinigt" ;;

                # Zusammenfassung
                "duration") echo "Dauer" ;;
                "updated_components") echo "Aktualisierte Komponenten" ;;
                "success_rate") echo "Erfolgsrate" ;;
                "minutes") echo "Minuten" ;;
                "seconds") echo "Sekunden" ;;
                "minute") echo "Minute" ;;
                "second") echo "Sekunde" ;;

                # Pre-Check
                "updates_found") echo "Updates gefunden" ;;
                "all_components_uptodate") echo "Alle Komponenten sind aktuell" ;;

                # Help/Options
                "app_name") echo "CachyOS Multi-Updater" ;;
                "version_label") echo "Version:" ;;
                "usage") echo "Verwendung:" ;;
                "options") echo "Optionen:" ;;
                "only_system") echo "Nur System-Updates (CachyOS)" ;;
                "only_aur") echo "Nur AUR-Updates" ;;
                "only_cursor") echo "Nur Cursor-Update" ;;
                "only_adguard") echo "Nur AdGuard Home-Update" ;;
                "only_flatpak") echo "Nur Flatpak-Updates" ;;
                "dry_run_desc") echo "Zeigt was gemacht würde, ohne Änderungen" ;;
                "interactive_desc") echo "Interaktiver Modus (wähle Updates aus)" ;;
                "stats_desc") echo "Zeige Update-Statistiken" ;;
                "version_desc") echo "Zeigt die Versionsnummer" ;;
                "help_desc") echo "Zeigt diese Hilfe" ;;
                "unknown_option") echo "Unbekannte Option:" ;;
                "use_help") echo "Verwende --help für Hilfe" ;;
                "dry_run_mode") echo "DRY-RUN MODUS: Es werden keine Änderungen vorgenommen!" ;;
                "planned_updates") echo "Geplante Updates:" ;;

                # Warnings/Errors
                "config_invalid_value") echo "WARNUNG: Ungültiger Wert für" ;;
                "config_expected") echo "(erwartet:" ;;
                "config_in_line") echo "in Zeile" ;;
                "config_of") echo "von" ;;
                "error_file_not_found") echo "Fehler:" ;;
                "error_not_found_in") echo "nicht gefunden in" ;;
                "error_occurred") echo "Ein Fehler ist aufgetreten!" ;;
                "error_report_created") echo "Fehler-Report erstellt:" ;;
                "please_check_report") echo "Bitte prüfe den Report für Details." ;;
                "unknown") echo "Unbekannt" ;;
                "log_file_not_available") echo "Log-Datei nicht verfügbar" ;;
                "no_config_file") echo "Keine Config-Datei vorhanden (Standard-Einstellungen)" ;;

                # Update Frequency
                "last_update_days_ago") echo "Letztes Update vor" ;;
                "days") echo "Tagen" ;;
                "day") echo "Tag" ;;
                "warning_last_update") echo "WARNUNG: Letztes Update vor" ;;
                "regular_updates_important") echo "Regelmäßige Updates sind wichtig für Sicherheit und Stabilität." ;;
                "recommendation_weekly") echo "Empfehlung: Updates wöchentlich durchführen" ;;

                # Error Report
                "error_report_title") echo "FEHLER-REPORT: CachyOS Multi-Updater" ;;
                "error_type") echo "Fehlertyp:" ;;
                "date_label") echo "Datum:" ;;
                "script_version_label") echo "Script Version:" ;;
                "system_information") echo "SYSTEM INFORMATION" ;;
                "os_label") echo "OS:" ;;
                "kernel_label") echo "Kernel:" ;;
                "user_label") echo "User:" ;;
                "hostname_label") echo "Hostname:" ;;
                "disk_label") echo "Disk:" ;;
                "memory_label") echo "Memory:" ;;
                "last_50_log_lines") echo "LETZTE 50 LOG-ZEILEN" ;;
                "configuration") echo "KONFIGURATION" ;;
                "end_error_report") echo "ENDE FEHLER-REPORT" ;;

                # Cursor
                "loading_cursor_deb") echo "Lade Cursor .deb für Versionsprüfung..." ;;
                "loading_cursor_deb_simple") echo "Lade Cursor .deb..." ;;
                "download_successful") echo "Download erfolgreich:" ;;
                "download_failed") echo "Download fehlgeschlagen!" ;;
                "download_too_small") echo "Download zu klein oder fehlgeschlagen!" ;;
                "cursor_running") echo "Cursor läuft noch (PID:" ;;
                "please_close_manually") echo "Bitte manuell schließen für sauberes Update" ;;
                "cursor_not_auto_closed") echo "(Cursor wird nicht automatisch geschlossen)" ;;
                "cursor_not_running") echo "Cursor läuft nicht" ;;
                "extraction_error") echo "Fehler beim Extrahieren!" ;;
                "data_extraction_error") echo "Fehler beim Extrahieren der Daten!" ;;
                "available_version") echo "Verfügbare Version:" ;;
                "cursor_already_current") echo "Cursor ist bereits aktuell" ;;
                "update_available_from_to") echo "Update verfügbar:" ;;

                # AdGuard
                "adguard_updated") echo "AdGuardHome updated:" ;;
                "adguard_current") echo "AdGuardHome ist aktuell" ;;
                "adguard_not_found") echo "AdGuardHome Binary nicht gefunden in:" ;;

                # Script Update
                "checking_script_version") echo "Script-Version prüfen..." ;;
                "version_check_failed") echo "Versionsprüfung fehlgeschlagen (keine Internetverbindung?)" ;;
                "new_version_available") echo "Neue Script-Version verfügbar:" ;;
                "auto_update_enabled") echo "Automatisches Update ist aktiviert." ;;
                "update_script_now") echo "Script jetzt aktualisieren? (j/N):" ;;
                "script_updated_successfully") echo "Script erfolgreich aktualisiert!" ;;
                "please_rerun_script") echo "Bitte Script erneut ausführen, um die neue Version zu verwenden." ;;
                "auto_update_failed") echo "Automatisches Update fehlgeschlagen!" ;;
                "please_update_manually") echo "Bitte manuell aktualisieren." ;;
                "update_skipped") echo "Update übersprungen." ;;
                "update_options") echo "Update-Optionen:" ;;
                "tip_auto_update") echo "Tipp: Setze ENABLE_AUTO_UPDATE=true in config.conf für automatische Updates" ;;
                "local_version") echo "Lokale Version:" ;;
                "script_current") echo "Script ist aktuell (Version" ;;

                # Interactive
                "interactive_mode") echo "INTERAKTIVER MODUS" ;;
                "which_components_update") echo "Welche Komponenten möchtest du aktualisieren?" ;;
                "system_pacman") echo "System (pacman)?" ;;
                "aur_yay_paru") echo "AUR (yay/paru)?" ;;
                "cursor_editor") echo "Cursor Editor?" ;;
                "adguard_home") echo "AdGuard Home?" ;;
                "flatpak") echo "Flatpak?" ;;
                "enabled") echo "aktiviert" ;;
                "selected_updates") echo "Ausgewählte Updates:" ;;
                "continue_question") echo "Fortfahren? (J/n):" ;;
                "cancelled") echo "Abgebrochen." ;;

                # Summary
                "update_completed_title") echo "UPDATE ABGESCHLOSSEN" ;;
                "duration_label") echo "Dauer:" ;;
                "system_label") echo "System:" ;;
                "aur_label") echo "AUR:" ;;
                "cursor_updated") echo "Cursor aktualisiert" ;;
                "adguard_updated_label") echo "AdGuard Home aktualisiert" ;;
                "all_components_current") echo "Alle Komponenten waren bereits aktuell" ;;

                # Statistics
                "no_stats_available") echo "Keine Statistiken verfügbar (erstes Update)" ;;
                "update_statistics") echo "UPDATE-STATISTIKEN" ;;
                "total_updates") echo "Gesamt-Updates:" ;;
                "successful") echo "Erfolgreich:" ;;
                "failed") echo "Fehlgeschlagen:" ;;
                "success_rate_label") echo "Erfolgsrate:" ;;
                "avg_duration") echo "Durchschn. Dauer:" ;;
                "last_update") echo "Letztes Update:" ;;
                "estimated_duration") echo "Geschätzte Dauer:" ;;
                "average_from") echo "(Durchschnitt aus" ;;
                "updates") echo "Updates)" ;;

                # Pre-Check
                "system_pacman_label") echo "System (pacman)..." ;;
                "aur_yay_paru_label") echo "AUR (yay/paru)..." ;;
                "cursor_editor_label") echo "Cursor Editor..." ;;
                "adguard_home_label") echo "AdGuard Home..." ;;
                "flatpak_label") echo "Flatpak..." ;;
                "available") echo "verfügbar" ;;
                "already_current") echo "Bereits aktuell" ;;
                "managed_by_pacman_aur") echo "Über pacman/AUR verwaltet (System-/AUR-Updates)" ;;
                "version_will_be_checked") echo "Version wird beim Update geprüft" ;;

                # Dry-Run
                "dry_run_completed") echo "DRY-RUN ABGESCHLOSSEN" ;;
                "no_changes_made") echo "Keine Änderungen wurden vorgenommen." ;;
                "run_without_dry_run") echo "Führe das Script ohne --dry-run aus, um Updates durchzuführen." ;;

                *) echo "$key" ;;
            esac
            ;;
        *)
            # English (default)
            case "$key" in
                # General
                "press_enter_to_close") echo "Press Enter to close the window" ;;
                "all_updates_completed") echo "All updates completed successfully!" ;;
                "sudo_required") echo "Sudo password required..." ;;
                "sudo_failed") echo "Sudo authentication failed!" ;;
                "checking_updates") echo "CHECKING AVAILABLE UPDATES..." ;;
                "update_process_starts") echo "UPDATE PROCESS STARTING" ;;
                "update_summary") echo "UPDATE COMPLETED" ;;
                "completed") echo "completed" ;;

                # Components
                "system_update") echo "System Update" ;;
                "system_updates") echo "System Updates (pacman)" ;;
                "aur_update") echo "AUR Update" ;;
                "aur_updates") echo "AUR Updates (yay/paru)" ;;
                "cursor_editor_update") echo "Cursor Editor Update" ;;
                "adguard_home_update") echo "AdGuard Home Update" ;;
                "flatpak_updates") echo "Flatpak Updates" ;;

                # Status
                "running") echo "running..." ;;
                "checking") echo "checking..." ;;
                "downloading") echo "Downloading" ;;
                "installing") echo "Installing update..." ;;
                "already_uptodate") echo "Already up to date" ;;
                "packages_available") echo "packages available" ;;
                "packages_updated") echo "packages updated" ;;
                "package") echo "package" ;;
                "packages") echo "packages" ;;
                "update_available") echo "Update available" ;;
                "updated") echo "Updated" ;;
                "not_installed") echo "not installed" ;;
                "skipped") echo "skipped" ;;
                "managed_by_pacman") echo "Managed by pacman" ;;

                # Cleanup
                "cleanup") echo "Cleanup..." ;;
                "system_cleaned") echo "System cleaned" ;;

                # Summary
                "duration") echo "Duration" ;;
                "updated_components") echo "Updated Components" ;;
                "success_rate") echo "Success Rate" ;;
                "minutes") echo "minutes" ;;
                "seconds") echo "seconds" ;;
                "minute") echo "minute" ;;
                "second") echo "second" ;;

                # Pre-Check
                "updates_found") echo "Updates found" ;;
                "all_components_uptodate") echo "All components are up to date" ;;

                # Help/Options
                "app_name") echo "CachyOS Multi-Updater" ;;
                "version_label") echo "Version:" ;;
                "usage") echo "Usage:" ;;
                "options") echo "Options:" ;;
                "only_system") echo "Only system updates (CachyOS)" ;;
                "only_aur") echo "Only AUR updates" ;;
                "only_cursor") echo "Only Cursor update" ;;
                "only_adguard") echo "Only AdGuard Home update" ;;
                "only_flatpak") echo "Only Flatpak updates" ;;
                "dry_run_desc") echo "Shows what would be done without making changes" ;;
                "interactive_desc") echo "Interactive mode (select updates)" ;;
                "stats_desc") echo "Show update statistics" ;;
                "version_desc") echo "Show version number" ;;
                "help_desc") echo "Show this help" ;;
                "unknown_option") echo "Unknown option:" ;;
                "use_help") echo "Use --help for help" ;;
                "dry_run_mode") echo "DRY-RUN MODE: No changes will be made!" ;;
                "planned_updates") echo "Planned updates:" ;;

                # Warnings/Errors
                "config_invalid_value") echo "WARNING: Invalid value for" ;;
                "config_expected") echo "(expected:" ;;
                "config_in_line") echo "in line" ;;
                "config_of") echo "of" ;;
                "error_file_not_found") echo "Error:" ;;
                "error_not_found_in") echo "not found in" ;;
                "error_occurred") echo "An error occurred!" ;;
                "error_report_created") echo "Error report created:" ;;
                "please_check_report") echo "Please check the report for details." ;;
                "unknown") echo "Unknown" ;;
                "log_file_not_available") echo "Log file not available" ;;
                "no_config_file") echo "No config file present (default settings)" ;;

                # Update Frequency
                "last_update_days_ago") echo "Last update" ;;
                "days") echo "days ago" ;;
                "day") echo "day ago" ;;
                "warning_last_update") echo "WARNING: Last update" ;;
                "regular_updates_important") echo "Regular updates are important for security and stability." ;;
                "recommendation_weekly") echo "Recommendation: Perform updates weekly" ;;

                # Error Report
                "error_report_title") echo "ERROR REPORT: CachyOS Multi-Updater" ;;
                "error_type") echo "Error type:" ;;
                "date_label") echo "Date:" ;;
                "script_version_label") echo "Script Version:" ;;
                "system_information") echo "SYSTEM INFORMATION" ;;
                "os_label") echo "OS:" ;;
                "kernel_label") echo "Kernel:" ;;
                "user_label") echo "User:" ;;
                "hostname_label") echo "Hostname:" ;;
                "disk_label") echo "Disk:" ;;
                "memory_label") echo "Memory:" ;;
                "last_50_log_lines") echo "LAST 50 LOG LINES" ;;
                "configuration") echo "CONFIGURATION" ;;
                "end_error_report") echo "END ERROR REPORT" ;;

                # Cursor
                "loading_cursor_deb") echo "Loading Cursor .deb for version check..." ;;
                "loading_cursor_deb_simple") echo "Loading Cursor .deb..." ;;
                "download_successful") echo "Download successful:" ;;
                "download_failed") echo "Download failed!" ;;
                "download_too_small") echo "Download too small or failed!" ;;
                "cursor_running") echo "Cursor is still running (PID:" ;;
                "please_close_manually") echo "Please close manually for clean update" ;;
                "cursor_not_auto_closed") echo "(Cursor will not be closed automatically)" ;;
                "cursor_not_running") echo "Cursor is not running" ;;
                "extraction_error") echo "Error extracting!" ;;
                "data_extraction_error") echo "Error extracting data!" ;;
                "available_version") echo "Available version:" ;;
                "cursor_already_current") echo "Cursor is already current" ;;
                "update_available_from_to") echo "Update available:" ;;

                # AdGuard
                "adguard_updated") echo "AdGuardHome updated:" ;;
                "adguard_current") echo "AdGuardHome is current" ;;
                "adguard_not_found") echo "AdGuardHome binary not found in:" ;;

                # Script Update
                "checking_script_version") echo "Checking script version..." ;;
                "version_check_failed") echo "Version check failed (no internet connection?)" ;;
                "new_version_available") echo "New script version available:" ;;
                "auto_update_enabled") echo "Automatic update is enabled." ;;
                "update_script_now") echo "Update script now? (y/N):" ;;
                "script_updated_successfully") echo "Script updated successfully!" ;;
                "please_rerun_script") echo "Please run the script again to use the new version." ;;
                "auto_update_failed") echo "Automatic update failed!" ;;
                "please_update_manually") echo "Please update manually." ;;
                "update_skipped") echo "Update skipped." ;;
                "update_options") echo "Update options:" ;;
                "tip_auto_update") echo "Tip: Set ENABLE_AUTO_UPDATE=true in config.conf for automatic updates" ;;
                "local_version") echo "Local version:" ;;
                "script_current") echo "Script is current (version" ;;

                # Interactive
                "interactive_mode") echo "INTERACTIVE MODE" ;;
                "which_components_update") echo "Which components do you want to update?" ;;
                "system_pacman") echo "System (pacman)?" ;;
                "aur_yay_paru") echo "AUR (yay/paru)?" ;;
                "cursor_editor") echo "Cursor Editor?" ;;
                "adguard_home") echo "AdGuard Home?" ;;
                "flatpak") echo "Flatpak?" ;;
                "enabled") echo "enabled" ;;
                "selected_updates") echo "Selected updates:" ;;
                "continue_question") echo "Continue? (Y/n):" ;;
                "cancelled") echo "Cancelled." ;;

                # Summary
                "update_completed_title") echo "UPDATE COMPLETED" ;;
                "duration_label") echo "Duration:" ;;
                "system_label") echo "System:" ;;
                "aur_label") echo "AUR:" ;;
                "cursor_updated") echo "Cursor updated" ;;
                "adguard_updated_label") echo "AdGuard Home updated" ;;
                "all_components_current") echo "All components were already current" ;;

                # Statistics
                "no_stats_available") echo "No statistics available (first update)" ;;
                "update_statistics") echo "UPDATE STATISTICS" ;;
                "total_updates") echo "Total updates:" ;;
                "successful") echo "Successful:" ;;
                "failed") echo "Failed:" ;;
                "success_rate_label") echo "Success rate:" ;;
                "avg_duration") echo "Avg. duration:" ;;
                "last_update") echo "Last update:" ;;
                "estimated_duration") echo "Estimated duration:" ;;
                "average_from") echo "(Average from" ;;
                "updates") echo "updates)" ;;

                # Pre-Check
                "system_pacman_label") echo "System (pacman)..." ;;
                "aur_yay_paru_label") echo "AUR (yay/paru)..." ;;
                "cursor_editor_label") echo "Cursor Editor..." ;;
                "adguard_home_label") echo "AdGuard Home..." ;;
                "flatpak_label") echo "Flatpak..." ;;
                "available") echo "available" ;;
                "already_current") echo "Already current" ;;
                "managed_by_pacman_aur") echo "Managed by pacman/AUR (System/AUR updates)" ;;
                "version_will_be_checked") echo "Version will be checked during update" ;;

                # Dry-Run
                "dry_run_completed") echo "DRY-RUN COMPLETED" ;;
                "no_changes_made") echo "No changes were made." ;;
                "run_without_dry_run") echo "Run the script without --dry-run to perform updates." ;;

                *) echo "$key" ;;
            esac
            ;;
    esac
}
