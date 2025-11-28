#!/bin/bash
#
# CachyOS Multi-Updater - Pre-Update Check Module
# Module for checking available updates before starting
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)
#
# This is free and open source software (FOSS).
# You are welcome to modify and distribute it under the terms of the MIT License.
#
# Repository: https://github.com/SunnyCueq/cachyos-multi-updater
#

# ========== Pre-Update Check ==========
check_available_updates() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${COLOR_BOLD}🔍 $(t 'checking_updates')${COLOR_RESET}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    local updates_found=false
    local total_packages=0

    # System-Updates prüfen
    if [ "$UPDATE_SYSTEM" = "true" ]; then
        echo -e "${COLOR_INFO}📦 $(t 'system_pacman_label')${COLOR_RESET}"
        
        # Verwende checkupdates für korrekte Paketanzahl
        # checkupdates gibt Exit-Code 2 zurück wenn keine Updates verfügbar sind
        local system_updates
        system_updates=$(checkupdates 2>/dev/null || true)
        local system_count=0
        
        if [ -n "$system_updates" ]; then
            system_count=$(echo "$system_updates" | wc -l)
            system_count=$(echo "$system_count" | tr -d '\n\r' | xargs)
        fi

        if [ "$system_count" -gt 0 ] 2>/dev/null; then
            echo -e "   ${COLOR_SUCCESS}✓${COLOR_RESET} $system_count $([ "$system_count" -eq 1 ] && echo "$(t 'package')" || echo "$(t 'packages')") $(t 'available')"
            updates_found=true
            total_packages=$((total_packages + system_count))
        else
            echo -e "   ${COLOR_WARNING}○${COLOR_RESET} $(t 'already_current')"
        fi
        echo ""
    fi

    # AUR-Updates prüfen
    if [ "$UPDATE_AUR" = "true" ]; then
        echo -e "${COLOR_INFO}🔧 $(t 'aur_yay_paru_label')${COLOR_RESET}"
        if command -v yay >/dev/null 2>&1; then
            local aur_updates
            aur_updates=$(yay -Qua 2>/dev/null || true)
            local aur_count=0
            
            if [ -n "$aur_updates" ]; then
                aur_count=$(echo "$aur_updates" | wc -l)
                aur_count=$(echo "$aur_count" | tr -d '\n\r' | xargs)
            fi

            if [ "$aur_count" -gt 0 ] 2>/dev/null; then
                echo -e "   ${COLOR_SUCCESS}✓${COLOR_RESET} $aur_count $([ "$aur_count" -eq 1 ] && echo "$(t 'package')" || echo "$(t 'packages')") $(t 'available')"
                updates_found=true
                total_packages=$((total_packages + aur_count))
            else
                echo -e "   ${COLOR_WARNING}○${COLOR_RESET} $(t 'already_current')"
            fi
        elif command -v paru >/dev/null 2>&1; then
            local aur_updates
            aur_updates=$(paru -Qua 2>/dev/null || true)
            local aur_count=0
            
            if [ -n "$aur_updates" ]; then
                aur_count=$(echo "$aur_updates" | wc -l)
                aur_count=$(echo "$aur_count" | tr -d '\n\r' | xargs)
            fi

            if [ "$aur_count" -gt 0 ] 2>/dev/null; then
                echo -e "   ${COLOR_SUCCESS}✓${COLOR_RESET} $aur_count $([ "$aur_count" -eq 1 ] && echo "$(t 'package')" || echo "$(t 'packages')") $(t 'available')"
                updates_found=true
                total_packages=$((total_packages + aur_count))
            else
                echo -e "   ${COLOR_WARNING}○${COLOR_RESET} $(t 'already_current')"
            fi
        else
            echo -e "   ${COLOR_WARNING}⊘${COLOR_RESET} $(t 'not_installed')"
        fi
        echo ""
    fi

    # Cursor-Update prüfen
    if [ "$UPDATE_CURSOR" = "true" ]; then
        echo -e "${COLOR_INFO}🖱️  $(t 'cursor_editor_label')${COLOR_RESET}"
        if command -v cursor >/dev/null 2>&1; then
            # Prüfe ob über pacman installiert
            if pacman -Q cursor 2>/dev/null | grep -q cursor; then
                echo -e "   ${COLOR_WARNING}○${COLOR_RESET} $(t 'managed_by_pacman_aur')"
            else
                # Über AUR installiert → prüfe AUR-Version vs. installierte Version
                # Versuche aktuelle installierte Version zu ermitteln
                CURSOR_PATH=$(which cursor)
                CURSOR_INSTALL_DIR=$(dirname "$(readlink -f "$CURSOR_PATH")")
                CURRENT_VERSION="unbekannt"

                if [ -f "$CURSOR_INSTALL_DIR/resources/app/package.json" ]; then
                    CURRENT_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$CURSOR_INSTALL_DIR/resources/app/package.json" 2>/dev/null | head -1 || echo "unbekannt")
                fi
                # Fallback: Prüfe alternative Pfade
                if [ "$CURRENT_VERSION" = "unbekannt" ]; then
                    for alt_path in "/opt/Cursor/resources/app/package.json" "/usr/share/cursor/resources/app/package.json" "$HOME/.local/share/cursor/resources/app/package.json"; do
                        if [ -f "$alt_path" ]; then
                            CURRENT_VERSION=$(grep -oP '"version":\s*"\K[0-9.]+' "$alt_path" 2>/dev/null | head -1 || echo "unbekannt")
                            [ "$CURRENT_VERSION" != "unbekannt" ] && break
                        fi
                    done
                fi

                # Prüfe AUR-Version
                if pacman -Q cursor-bin 2>/dev/null | grep -q cursor-bin; then
                    CURSOR_AUR_VERSION_FULL=$(pacman -Q cursor-bin | awk '{print $2}')
                    CURSOR_AUR_VERSION=$(echo "$CURSOR_AUR_VERSION_FULL" | sed 's/-.*$//')
                    
                    if [ "$CURRENT_VERSION" != "unbekannt" ]; then
                        # Vergleiche installierte Version mit AUR-Version (semantischer Vergleich)
                        # Verwende sort -V für semantischen Versionsvergleich
                        if [ "$CURRENT_VERSION" = "$CURSOR_AUR_VERSION" ]; then
                            echo -e "   ${COLOR_WARNING}○${COLOR_RESET} $(t 'already_current') (v$CURRENT_VERSION, über AUR installiert)"
                        else
                            # Prüfe ob installierte Version älter ist
                            if printf '%s\n%s\n' "$CURRENT_VERSION" "$CURSOR_AUR_VERSION" | sort -V | head -1 | grep -q "^$CURRENT_VERSION$"; then
                                # CURRENT_VERSION ist älter
                                echo -e "   ${COLOR_SUCCESS}✓${COLOR_RESET} $(t 'update_available_from_to') $CURRENT_VERSION → $CURSOR_AUR_VERSION (AUR-Update verfügbar)"
                                updates_found=true
                                total_packages=$((total_packages + 1))
                            else
                                # CURRENT_VERSION ist neuer (sollte nicht passieren, aber sicherheitshalber)
                                echo -e "   ${COLOR_WARNING}○${COLOR_RESET} $(t 'already_current') (v$CURRENT_VERSION, über AUR installiert, AUR: v$CURSOR_AUR_VERSION)"
                            fi
                        fi
                    else
                        echo -e "   ${COLOR_WARNING}?${COLOR_RESET} $(t 'version_will_be_checked') (AUR: v$CURSOR_AUR_VERSION)"
                    fi
                else
                    echo -e "   ${COLOR_WARNING}?${COLOR_RESET} $(t 'version_will_be_checked')"
                fi
            fi
        else
            echo -e "   ${COLOR_WARNING}⊘${COLOR_RESET} $(t 'not_installed')"
        fi
        echo ""
    fi

    # AdGuard Home-Update prüfen
    if [ "$UPDATE_ADGUARD" = "true" ]; then
        echo -e "${COLOR_INFO}🛡️  $(t 'adguard_home_label')${COLOR_RESET}"
        
        # Prüfe Installationsmethode
        if pacman -Q adguard-home 2>/dev/null | grep -q adguard-home; then
            echo -e "   ${COLOR_WARNING}○${COLOR_RESET} $(t 'managed_by_pacman_aur')"
        elif pacman -Q adguard-home-bin 2>/dev/null | grep -q adguard-home-bin || pacman -Q adguardhome 2>/dev/null | grep -q adguardhome; then
            echo -e "   ${COLOR_WARNING}○${COLOR_RESET} $(t 'managed_by_pacman_aur')"
        elif [[ -f "$HOME/AdGuardHome/AdGuardHome" ]]; then
            # Manuell installiert → prüfe auf Updates
            current_version=$(cd "$HOME/AdGuardHome" && ./AdGuardHome --version 2>/dev/null | grep -oP 'v\K[0-9.]+' || echo "0.0.0")
            latest_version=$(curl -s "https://api.github.com/repos/AdguardTeam/AdGuardHome/releases/latest" 2>/dev/null | grep -oP '"tag_name":\s*"v\K[0-9.]+' | head -1 || echo "")

            if [ -n "$latest_version" ]; then
                if [ "$current_version" = "$latest_version" ]; then
                    echo -e "   ${COLOR_WARNING}○${COLOR_RESET} $(t 'already_current') (v$current_version)"
                else
                    echo -e "   ${COLOR_SUCCESS}✓${COLOR_RESET} $(t 'update_available_from_to') v$current_version → v$latest_version"
                    updates_found=true
                    total_packages=$((total_packages + 1))
                fi
            else
                echo -e "   ${COLOR_WARNING}?${COLOR_RESET} $(t 'version_will_be_checked')"
            fi
        else
            echo -e "   ${COLOR_WARNING}⊘${COLOR_RESET} $(t 'not_installed')"
        fi
        echo ""
    fi

    # Flatpak-Updates prüfen
    if [ "$UPDATE_FLATPAK" = "true" ]; then
        echo -e "${COLOR_INFO}📦 $(t 'flatpak_label')${COLOR_RESET}"
        if command -v flatpak >/dev/null 2>&1; then
            local flatpak_updates
            flatpak_updates=$(flatpak remote-ls --updates 2>/dev/null || true)
            local flatpak_count=0
            
            if [ -n "$flatpak_updates" ]; then
                flatpak_count=$(echo "$flatpak_updates" | wc -l)
                flatpak_count=$(echo "$flatpak_count" | tr -d '\n\r' | xargs)
            fi

            if [ "$flatpak_count" -gt 0 ] 2>/dev/null; then
                echo -e "   ${COLOR_SUCCESS}✓${COLOR_RESET} $flatpak_count $([ "$flatpak_count" -eq 1 ] && echo "$(t 'package')" || echo "$(t 'packages')") $(t 'available')"
                updates_found=true
                total_packages=$((total_packages + flatpak_count))
            else
                echo -e "   ${COLOR_WARNING}○${COLOR_RESET} $(t 'already_current')"
            fi
        else
            echo -e "   ${COLOR_WARNING}⊘${COLOR_RESET} $(t 'not_installed')"
        fi
        echo ""
    fi

    # Zusammenfassung
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ "$updates_found" = "true" ]; then
        if [ "$total_packages" -gt 0 ]; then
            local package_text
            if [ "$total_packages" -eq 1 ]; then
                package_text=$(t 'package')
            else
                package_text=$(t 'packages')
            fi
            echo -e "${COLOR_SUCCESS}✓ $(t 'updates_found'): $total_packages $package_text${COLOR_RESET}"
        else
            echo -e "${COLOR_SUCCESS}✓ $(t 'updates_found')${COLOR_RESET}"
        fi
    else
        echo -e "${COLOR_WARNING}○ $(t 'all_components_uptodate')${COLOR_RESET}"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Kurze Pause für Lesbarkeit
    sleep 2
}
