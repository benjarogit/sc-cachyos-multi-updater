[![Version](https://img.shields.io/badge/version-2.3.0-blue)](https://github.com/benjarogit/sc-cachyos-multi-updater/releases)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org)
[![PyQt6](https://img.shields.io/pypi/pyversions/PyQt6)](https://pypi.org/project/PyQt6/)
[![Lizenz](https://img.shields.io/badge/Lizenz-MIT-green)](LICENSE)
[![Downloads](https://img.shields.io/github/downloads/benjarogit/sc-cachyos-multi-updater/total)](https://github.com/benjarogit/sc-cachyos-multi-updater/releases)

# CachyOS Multi-Updater

Ein modernes PyQt6-Tool, mit dem du unter CachyOS / Arch Linux **alle Paketquellen gleichzeitig** aktualisieren kannst – pacman, flatpak, snap, aura, yay, pikaur, paru und mehr – mit nur einem Klick.

> **Sprache / Language:** [🇩🇪 Deutsch](README.de.md) | [🇬🇧 English](README.md)

## Features

- ✅ **Gleichzeitige Updates** - Alle unterstützten Paket-Manager auf einmal aktualisieren
- ✅ **Live-Log-Ansicht** - Echtzeit-Ausgabe mit farbiger Hervorhebung
- ✅ **Dark / Light / Auto-Theme** - Passt sich automatisch deinem System-Theme an
- ✅ **Vollständige Lokalisierung** - Komplette Deutsch-/Englisch-Übersetzung
- ✅ **Konfigurationsdialog** - Umfassende Einstellungen mit Validierung
- ✅ **Automatische Versionsprüfung** - Prüft bei Start auf Updates
- ✅ **Sicherer Bash-Wrapper** - Verwendet shlex.quote, keine unsicheren shell=True Aufrufe
- ✅ **Type Hints** - 100% typisierter Code für bessere Wartbarkeit
- ✅ **Umfassende Tests** - 44+ Unit-Tests mit 13% Coverage
- ✅ **Moderne Architektur** - Sauberer Code, Best Practices, Performance-Optimierungen

## Screenshots

![Hero](screenshots/hero.png)

<details>
<summary>Weitere Screenshots (klick zum Aufklappen)</summary>

![Thumb 1](screenshots/thumb-1.png) ![Thumb 2](screenshots/thumb-2.png) ![Thumb 3](screenshots/thumb-3.png)  
![Thumb 4](screenshots/thumb-4.png) ![Thumb 5](screenshots/thumb-5.png) ![Thumb 6](screenshots/thumb-6.png)

</details>

## Systemvoraussetzungen

- CachyOS oder jede Arch-Linux-Distribution
- Python 3.11 oder neuer
- PyQt6 ≥ 6.7
- sudo-Berechtigungen für Paket-Manager

## Installation

```bash
git clone https://github.com/benjarogit/sc-cachyos-multi-updater.git
cd sc-cachyos-multi-updater
python -m venv venv
source venv/bin/activate
pip install -r cachyos-multi-updater/requirements-gui.txt
```

### Quick Start

1. **Repository klonen:**
   ```bash
   git clone https://github.com/benjarogit/sc-cachyos-multi-updater.git
   cd sc-cachyos-multi-updater
   ```

2. **Setup ausführen (empfohlen für Erstinstallation):**
   ```bash
   cd cachyos-multi-updater
   ./setup.sh
   ```
   Dies führt dich durch die Konfiguration und erstellt eine Desktop-Verknüpfung.

3. **Updates starten:**
   ```bash
   ./cachyos-update-gui
   ```
   Oder verwende die während des Setups erstellte Desktop-Verknüpfung.

## Konfiguration

Das Tool kann über `cachyos-multi-updater/config.conf` angepasst werden. Kopiere von `config.conf.example` und bearbeite nach Bedarf.

### Umgebungsvariablen

- `SCRIPT_DIR` - Pfad zum Script-Verzeichnis (falls GUI update-all.sh nicht findet)
- `GUI_LANGUAGE` - Sprache überschreiben (`de`, `en`, oder `auto`)
- `GUI_THEME` - Theme überschreiben (`light`, `dark`, oder `auto`)

### Konfigurationsdatei-Optionen

| Option | Werte | Standard | Beschreibung |
|--------|-------|---------|-------------|
| `ENABLE_SYSTEM_UPDATE` | `true`/`false` | `true` | System-Paket-Updates aktivieren |
| `ENABLE_AUR_UPDATE` | `true`/`false` | `true` | AUR-Paket-Updates aktivieren |
| `ENABLE_CURSOR_UPDATE` | `true`/`false` | `true` | Cursor Editor-Updates aktivieren |
| `ENABLE_FLATPAK_UPDATE` | `true`/`false` | `true` | Flatpak-Anwendungs-Updates aktivieren |
| `ENABLE_ADGUARD_UPDATE` | `true`/`false` | `true` | AdGuard Home-Updates aktivieren |
| `ENABLE_NOTIFICATIONS` | `true`/`false` | `true` | Desktop-Benachrichtigungen anzeigen |
| `ENABLE_COLORS` | `true`/`false` | `true` | Farbige Terminal-Ausgabe |
| `DRY_RUN` | `true`/`false` | `false` | Immer im Vorschau-Modus laufen |
| `MAX_LOG_FILES` | Zahl | `10` | Anzahl der zu behaltenden Log-Dateien |
| `DOWNLOAD_RETRIES` | Zahl | `3` | Fehlgeschlagene Downloads N-mal wiederholen |
| `GUI_LANGUAGE` | `auto`/`de`/`en` | `auto` | GUI-Sprache |
| `GUI_THEME` | `auto`/`light`/`dark` | `auto` | GUI-Theme |

### Beispiel-Konfiguration

```ini
# Komponenten aktivieren/deaktivieren
ENABLE_SYSTEM_UPDATE=true
ENABLE_AUR_UPDATE=true
ENABLE_CURSOR_UPDATE=true
ENABLE_FLATPAK_UPDATE=true
ENABLE_ADGUARD_UPDATE=false

# Logging
MAX_LOG_FILES=10

# Benachrichtigungen
ENABLE_NOTIFICATIONS=true

# Sicherheit
DRY_RUN=false

# Erscheinungsbild
ENABLE_COLORS=true
GUI_THEME=auto
GUI_LANGUAGE=auto

# Downloads
DOWNLOAD_RETRIES=3
```

## Verwendung

### GUI-Version (Empfohlen)

**GUI starten:**
```bash
./cachyos-update-gui
```

Oder verwende die während des Setups erstellte Desktop-Verknüpfung.

**GUI-Features:**
- Komponenten-Auswahl per Checkboxen
- Echtzeit-Ausgabe mit Farben
- Fortschrittsbalken (0-100%)
- Einstellungsdialog mit 6 Tabs
- Log-Viewer
- Sichere Passwort-Verwaltung
- Toast-Benachrichtigungen

### Kommandozeilen-Version

**Update-Script direkt ausführen:**
```bash
cd cachyos-multi-updater
./update-all.sh
```

**Befehlszeilen-Optionen:**

| Option | Beschreibung |
|--------|-------------|
| `./update-all.sh` | Standard-Update (alle Komponenten) |
| `--only-system` | Nur System-Pakete |
| `--only-aur` | Nur AUR-Pakete |
| `--only-cursor` | Nur Cursor Editor |
| `--only-flatpak` | Nur Flatpak-Anwendungen |
| `--only-adguard` | Nur AdGuard Home |
| `--dry-run` | Vorschau ohne Änderungen |
| `--interactive` oder `-i` | Wähle was aktualisiert werden soll |
| `--stats` | Zeige Update-Statistiken |
| `--version` oder `-v` | Zeige Version |
| `--help` oder `-h` | Zeige Hilfe |

**Beispiele:**

```bash
# Vorschau was aktualisiert würde
./update-all.sh --dry-run

# Nur System-Pakete aktualisieren
./update-all.sh --only-system

# Interaktiver Modus
./update-all.sh --interactive

# Statistiken anzeigen
./update-all.sh --stats
```

## Fehlerbehebung

### Häufige Probleme

#### Script sagt "Update läuft bereits"

**Lösung:** Lösche die Lock-Datei:
```bash
rm cachyos-multi-updater/.update-all.lock
```

#### "Permission denied" beim Ausführen des Scripts

**Lösung:** Mache es ausführbar:
```bash
chmod +x cachyos-update-gui
chmod +x cachyos-multi-updater/update-all.sh
chmod +x cachyos-multi-updater/setup.sh
```

#### GUI startet nicht

**Prüfen:**
1. PyQt6 installiert? `python3 -c "from PyQt6.QtWidgets import QApplication"`
2. Python-Version 3.11+? `python3 --version`
3. Abhängigkeiten installiert? `pip3 install -r cachyos-multi-updater/requirements-gui.txt`

**Lösung:**
```bash
# PyQt6 installieren
pip3 install PyQt6

# Oder alle Abhängigkeiten installieren
pip3 install -r cachyos-multi-updater/requirements-gui.txt
```

#### GUI zeigt "Script nicht gefunden"

**Lösung:** Die GUI muss `update-all.sh` finden. Stelle sicher:
1. Du läufst vom Projekt-Root: `./cachyos-update-gui`
2. Oder setze Environment-Variable: `export SCRIPT_DIR=/path/to/cachyos-multi-updater`
3. Prüfe dass `cachyos-multi-updater/update-all.sh` existiert

### Hilfe erhalten

1. **Logs zuerst prüfen** - Die meisten Probleme sind in `cachyos-multi-updater/logs/` geloggt
2. **Dry-Run-Modus versuchen** - Siehe was passieren würde: `./cachyos-multi-updater/update-all.sh --dry-run`
3. **Fehlerbehebungs-Abschnitt prüfen** - Dein Problem könnte oben aufgeführt sein
4. **GitHub-Issue erstellen** - Füge Log-Ausschnitte hinzu und beschreibe was du versucht hast

## Beitragen

Verbesserungen und Fehlerberichte sind willkommen! Bitte erstelle ein Issue oder Pull Request auf [GitHub](https://github.com/benjarogit/sc-cachyos-multi-updater).

### Entwicklungsumgebung

```bash
git clone https://github.com/benjarogit/sc-cachyos-multi-updater.git
cd sc-cachyos-multi-updater
python -m venv venv
source venv/bin/activate
pip install -r cachyos-multi-updater/requirements-gui.txt
pip install pytest pytest-cov pytest-qt
```

### Tests ausführen

```bash
cd cachyos-multi-updater
pytest gui/tests/ -v --cov=gui/core --cov=gui/utils --cov=gui/dialogs --cov=gui/widgets
```

## Lizenz

Dieses Projekt ist Open Source. Du kannst es frei verwenden, modifizieren und unter den Bedingungen der MIT-Lizenz verteilen.

## Links

- **GitHub Repository:** https://github.com/benjarogit/sc-cachyos-multi-updater
- **Issues:** https://github.com/benjarogit/sc-cachyos-multi-updater/issues
- **Releases:** https://github.com/benjarogit/sc-cachyos-multi-updater/releases

---

**Viel Erfolg mit deinen Updates! 🎉**
