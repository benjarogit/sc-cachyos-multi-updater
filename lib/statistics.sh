#!/bin/bash
#
# CachyOS Multi-Updater - Statistics Module
# Module for tracking update statistics and history
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)
#
# This is free and open source software (FOSS).
# You are welcome to modify and distribute it under the terms of the MIT License.
#
# Repository: https://github.com/SunnyCueq/cachyos-multi-updater
#

# ========== Update-Statistiken ==========
load_stats() {
    if [ -f "$STATS_FILE" ]; then
        cat "$STATS_FILE"
    else
        echo '{"total_updates":0,"total_duration":0,"last_update":"","successful_updates":0,"failed_updates":0}'
    fi
}

save_stats() {
    local duration="$1"
    local success="$2"

    local stats
    stats=$(load_stats)
    local total_updates
    total_updates=$(echo "$stats" | grep -oP '"total_updates":\s*\K[0-9]+' || echo "0")
    local total_duration
    total_duration=$(echo "$stats" | grep -oP '"total_duration":\s*\K[0-9]+' || echo "0")
    local successful
    successful=$(echo "$stats" | grep -oP '"successful_updates":\s*\K[0-9]+' || echo "0")
    local failed
    failed=$(echo "$stats" | grep -oP '"failed_updates":\s*\K[0-9]+' || echo "0")

    total_updates=$((total_updates + 1))
    total_duration=$((total_duration + duration))

    if [ "$success" = "true" ]; then
        successful=$((successful + 1))
    else
        failed=$((failed + 1))
    fi

    local avg_duration=$((total_duration / total_updates))

    cat > "$STATS_FILE" <<EOF
{
    "total_updates": $total_updates,
    "total_duration": $total_duration,
    "avg_duration": $avg_duration,
    "last_update": "$(date -Iseconds)",
    "successful_updates": $successful,
    "failed_updates": $failed,
    "last_duration": $duration
}
EOF

    log_info "Statistiken gespeichert: Update #$total_updates"
}

show_stats() {
    if [ ! -f "$STATS_FILE" ]; then
        echo "ℹ️  Keine Statistiken verfügbar (erstes Update)"
        return 0
    fi

    local stats
    stats=$(load_stats)
    local total_updates
    total_updates=$(echo "$stats" | grep -oP '"total_updates":\s*\K[0-9]+' || echo "0")
    local avg_duration
    avg_duration=$(echo "$stats" | grep -oP '"avg_duration":\s*\K[0-9]+' || echo "0")
    local successful
    successful=$(echo "$stats" | grep -oP '"successful_updates":\s*\K[0-9]+' || echo "0")
    local failed
    failed=$(echo "$stats" | grep -oP '"failed_updates":\s*\K[0-9]+' || echo "0")
    local last_update
    last_update=$(echo "$stats" | grep -oP '"last_update":\s*"\K[^"]+' || echo "Nie")

    local success_rate=0
    if [ "$total_updates" -gt 0 ]; then
        success_rate=$((successful * 100 / total_updates))
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${COLOR_BOLD}📊 UPDATE-STATISTIKEN${COLOR_RESET}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Gesamt-Updates:     $total_updates"
    echo -e "   Erfolgreich:        ${COLOR_SUCCESS}$successful${COLOR_RESET}"
    echo -e "   Fehlgeschlagen:     ${COLOR_ERROR}$failed${COLOR_RESET}"
    echo "   Erfolgsrate:        $success_rate%"
    echo "   Durchschn. Dauer:   $((avg_duration / 60))m $((avg_duration % 60))s"
    echo "   Letztes Update:     $(date -d "$last_update" '+%d.%m.%Y %H:%M' 2>/dev/null || echo "$last_update")"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

estimate_duration() {
    if [ ! -f "$STATS_FILE" ]; then
        return 0
    fi

    local stats
    stats=$(load_stats)
    local avg_duration
    avg_duration=$(echo "$stats" | grep -oP '"avg_duration":\s*\K[0-9]+' || echo "0")
    local total_updates
    total_updates=$(echo "$stats" | grep -oP '"total_updates":\s*\K[0-9]+' || echo "0")

    if [ "$avg_duration" -gt 0 ] && [ "$total_updates" -ge 3 ]; then
        local minutes=$((avg_duration / 60))
        local seconds=$((avg_duration % 60))
        echo ""
        echo "⏱️  Geschätzte Dauer: ~${minutes}m ${seconds}s"
        echo "   (Durchschnitt aus $total_updates Updates)"
        echo ""
    fi
}
