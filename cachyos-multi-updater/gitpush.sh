#!/bin/bash
#
# CachyOS Multi-Updater - Git Push & Release Script
# Automatisiert: Git Commit, Push, Tag und GitHub Release
#
# Copyright (c) 2024-2025 SunnyCueq
# Licensed under the MIT License (see LICENSE file)
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory (where gitpush.sh is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Root directory (parent of cachyos-multi-updater/)
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

# Read version from update-all.sh (in cachyos-multi-updater/)
UPDATE_SCRIPT="${SCRIPT_DIR}/update-all.sh"
if [ ! -f "${UPDATE_SCRIPT}" ]; then
    echo -e "${RED}❌ Fehler: update-all.sh nicht gefunden in ${SCRIPT_DIR}${NC}"
    exit 1
fi

VERSION=$(grep -oP 'readonly SCRIPT_VERSION="\K[^"]+' "${UPDATE_SCRIPT}" || echo "")
if [ -z "$VERSION" ]; then
    echo -e "${RED}❌ Fehler: Version nicht in update-all.sh gefunden${NC}"
    exit 1
fi

DATE=$(date +%Y-%m-%d)
REPO="benjarogit/sc-cachyos-multi-updater"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Git Push & Release Script${NC}"
echo -e "${GREEN}Version: ${VERSION}${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check if git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Fehler: Kein Git-Repository gefunden${NC}"
    exit 1
fi

# Check if there are changes
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠ Keine Änderungen zum Committen${NC}"
    exit 0
fi

# Show status
echo -e "${YELLOW}[1/6] Git Status:${NC}"
git status --short
echo ""

# Ask for commit message
if [ -z "$1" ]; then
    echo -e "${YELLOW}Commit-Message (leer = automatisch):${NC}"
    read -r COMMIT_MESSAGE
else
    COMMIT_MESSAGE="$1"
fi

# Default commit message
if [ -z "$COMMIT_MESSAGE" ]; then
    COMMIT_MESSAGE="Version ${VERSION} - $(date +%Y-%m-%d)"
fi

# Commit
echo -e "${YELLOW}[2/6] Committing changes...${NC}"
git add -A

# Exclude files that shouldn't be committed
EXCLUDE_FILES=(
    "CODE_QUALITY_REPORT.md"
    "FINAL_AUDIT_REPORT.md"
    "GUI_RELEASE_CHECK.md"
    "RISK_ASSESSMENT_REPORT.md"
    "IMPROVEMENTS.md"
    "RELEASE_*.md"
    "config.conf"
    "*.log"
    "cachyos-multi-updater/config.conf"
)

for file in "${EXCLUDE_FILES[@]}"; do
    git reset HEAD "$file" 2>/dev/null || true
done

git commit -m "${COMMIT_MESSAGE}"
echo -e "${GREEN}✓ Committed: ${COMMIT_MESSAGE}${NC}\n"

# Push
echo -e "${YELLOW}[3/6] Pushing to remote...${NC}"
git push
echo -e "${GREEN}✓ Pushed to remote${NC}\n"

# Determine release version
# REGEL: Lokale Version ist immer eine Version unter der GitHub-Version
# Dies ermöglicht Simulation von Tool-Updates (Update-Check findet höhere Version)
echo -e "${CYAN}Lokale Version: ${VERSION}${NC}"

# Calculate suggested release version (local version + 1 patch)
# Extract version parts
IFS='.' read -ra VERSION_PARTS <<< "$VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

# Increment patch version
PATCH=$((PATCH + 1))
SUGGESTED_VERSION="${MAJOR}.${MINOR}.${PATCH}"

echo -e "${CYAN}Vorgeschlagene Release-Version: ${SUGGESTED_VERSION}${NC}"
echo -e "${YELLOW}Release-Version (Enter = ${SUGGESTED_VERSION}, oder eigene Version):${NC}"
read -r RELEASE_VERSION

if [ -z "$RELEASE_VERSION" ]; then
    RELEASE_VERSION="$SUGGESTED_VERSION"
fi

# Warn if release version is lower or equal to local version
if [ "$(printf '%s\n' "$VERSION" "$RELEASE_VERSION" | sort -V | head -n1)" = "$RELEASE_VERSION" ] && [ "$VERSION" != "$RELEASE_VERSION" ]; then
    echo -e "${YELLOW}⚠ Warnung: Release-Version (${RELEASE_VERSION}) ist niedriger als lokale Version (${VERSION})${NC}"
    echo -e "${YELLOW}   Regel: Lokale Version sollte immer unter GitHub-Version sein!${NC}"
fi

# Create release tag
TAG_NAME="v${RELEASE_VERSION}"
echo -e "${YELLOW}[4/6] Creating release tag...${NC}"

# Check if tag already exists
if git rev-parse "${TAG_NAME}" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Tag ${TAG_NAME} existiert bereits${NC}"
    echo -e "${YELLOW}   Überspringe Tag-Erstellung${NC}"
else
    # Create annotated tag
    git tag -a "${TAG_NAME}" -m "Version ${RELEASE_VERSION} - ${DATE}"
    
    # Push tag
    git push origin "${TAG_NAME}"
    echo -e "${GREEN}✓ Release tag ${TAG_NAME} erstellt und gepusht${NC}"
fi

# Create GitHub Release
echo -e "${YELLOW}[5/6] Creating GitHub Release...${NC}"

# Check if gh CLI is available
if command -v gh &> /dev/null; then
    # Try to find changelog file
    CHANGELOG_FILE=""
    for file in RELEASE_*.md cachyos-multi-updater/RELEASE_*.md; do
        if [ -f "$file" ]; then
            CHANGELOG_FILE="$file"
            break
        fi
    done
    
    # Extract changelog if file exists
    if [ -n "$CHANGELOG_FILE" ] && [ -f "$CHANGELOG_FILE" ]; then
        RELEASE_NOTES=$(cat "$CHANGELOG_FILE")
    else
        RELEASE_NOTES="Version ${RELEASE_VERSION} - ${DATE}

See GitHub Releases for full changelog."
    fi
    
    # Check if release already exists
    if gh release view "${TAG_NAME}" >/dev/null 2>&1; then
        # Update existing release
        echo "$RELEASE_NOTES" | gh release edit "${TAG_NAME}" --notes-file - 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ GitHub Release ${TAG_NAME} aktualisiert${NC}"
        else
            echo -e "${YELLOW}⚠ GitHub Release ${TAG_NAME} konnte nicht aktualisiert werden${NC}"
        fi
    else
        # Create new release
        echo "$RELEASE_NOTES" | gh release create "${TAG_NAME}" --title "Version ${RELEASE_VERSION}" --notes-file - 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ GitHub Release ${TAG_NAME} erstellt${NC}"
        else
            echo -e "${YELLOW}⚠ GitHub Release ${TAG_NAME} konnte nicht erstellt werden${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠ GitHub CLI (gh) nicht gefunden${NC}"
    echo -e "${YELLOW}   Installiere mit: sudo pacman -S github-cli${NC}"
    echo -e "${YELLOW}   Oder erstelle Release manuell auf GitHub${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Git Push & Release abgeschlossen!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Lokale Version: ${VERSION}${NC}"
echo -e "${GREEN}Release Version: ${RELEASE_VERSION}${NC}"
echo -e "${GREEN}Tag: ${TAG_NAME}${NC}"
echo -e "${GREEN}========================================${NC}\n"
