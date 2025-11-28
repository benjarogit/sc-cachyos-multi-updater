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

                *) echo "$key" ;;
            esac
            ;;
    esac
}
