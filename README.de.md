# CachyOS Multi-Updater

> **Sprache / Language:** [🇩🇪 Deutsch](README.de.md) | [🇬🇧 English](README.md)

Ein einfaches One-Click-Update-Tool für CachyOS, das automatisch System-Pakete, AUR-Pakete, den Cursor Editor, Flatpak-Anwendungen und AdGuard Home aktualisiert.

---

## 🚀 Quick Start

### Installation (3 Schritte)

1. **Repository klonen:**
   ```bash
   git clone https://github.com/benjarogit/sc-cachyos-multi-updater.git
   cd sc-cachyos-multi-updater
   ```

2. **Setup ausführen (empfohlen für Erstinstallation):**
   ```bash
   ./cachyos-update
   ```
   Wähle Option `1` um das Setup auszuführen, das dich durch die Konfiguration führt und eine Desktop-Verknüpfung erstellt.

3. **Updates starten:**
   ```bash
   ./cachyos-update
   ```
   Wähle Option `2` um Updates zu starten.

### Start-Kommandos

**Console-Version (mit Menü):**
```bash
./cachyos-update
```

**GUI-Version:**
```bash
./cachyos-update-gui
```

### Grundlegende Konfiguration

Erstelle `cachyos-multi-updater/config.conf` aus dem Beispiel:
```bash
cp cachyos-multi-updater/config.conf.example cachyos-multi-updater/config.conf
```

Bearbeite um Komponenten zu aktivieren/deaktivieren:
```ini
ENABLE_SYSTEM_UPDATE=true
ENABLE_AUR_UPDATE=true
ENABLE_CURSOR_UPDATE=true
ENABLE_FLATPAK_UPDATE=true
ENABLE_ADGUARD_UPDATE=true
```

---

## 🤔 Was ist das?

**CachyOS Multi-Updater** ist ein Script, das dir hilft, dein CachyOS Linux-System auf dem neuesten Stand zu halten. Anstatt verschiedene Teile deines Systems manuell nacheinander zu aktualisieren, macht dieses Script alles automatisch in einem Durchgang.

**Verfügbar in zwei Versionen:**
- **Console-Version** - Kommandozeilen-Interface mit Menü-System
- **GUI-Version** - Moderne Qt-basierte grafische Oberfläche (empfohlen für Anfänger)

### Was ist CachyOS?

CachyOS ist ein Linux-Betriebssystem, das auf Arch Linux basiert. Es ist darauf ausgelegt, schnell und für Performance optimiert zu sein. Wie jedes Betriebssystem benötigt es regelmäßige Updates, um Sicherheitskorrekturen, neue Features und Fehlerbehebungen zu erhalten.

### Warum brauche ich das?

Normalerweise erfordert das Aktualisieren eines Linux-Systems das Ausführen mehrerer Befehle:
- System-Pakete aktualisieren
- AUR-Pakete aktualisieren (Community-erstellte Software)
- Anwendungen wie den Cursor Editor aktualisieren
- Dienste wie AdGuard Home aktualisieren

Dieses Script macht all das automatisch und spart dir Zeit, während es sicherstellt, dass alles aktuell bleibt.

---

## ✨ Features

- ✅ **System-Updates** - Aktualisiert CachyOS-Pakete via pacman
- ✅ **AUR-Updates** - Aktualisiert AUR-Pakete via yay/paru
- ✅ **Cursor Editor** - Automatischer Download und Update (Versionsprüfung vor Download)
- ✅ **Flatpak-Anwendungen** - Aktualisiert alle Flatpak-Apps und Laufzeiten
- ✅ **AdGuard Home** - Automatisches Update mit Konfigurations-Backup
- ✅ **Automatische Bereinigung** - Entfernt alte Pakete, Caches und temporäre Dateien
- ✅ **GUI-Version** - Moderne Qt-basierte grafische Oberfläche mit Echtzeit-Fortschritt, sicherer Passwort-Verwaltung, Log-Viewer und umfassendem Einstellungs-Dialog
- ✅ **Interaktiver Modus** - Wähle was aktualisiert werden soll
- ✅ **Dry-Run-Modus** - Vorschau der Änderungen ohne sie durchzuführen
- ✅ **Statistiken** - Verfolge Update-Historie und Erfolgsraten
- ✅ **Logging** - Detaillierte Logs für Fehlerbehebung
- ✅ **Benachrichtigungen** - Desktop-Benachrichtigungen bei Update-Abschluss

---

## 📋 Voraussetzungen

### Erforderlich:
- **CachyOS oder Arch Linux**
- **sudo-Berechtigungen**
- **Internetverbindung**

### Optional:
- **AUR-Helper** (yay oder paru) - für AUR-Paket-Updates
- **Cursor Editor** - für Cursor-Updates
- **AdGuard Home** - für AdGuard-Updates (muss in `~/AdGuardHome` sein)
- **PyQt6** - für GUI-Version (`pip3 install PyQt6`)

---

## 🔧 Installationsanleitung

### Schritt 1: Download

**Option A: Mit Git (empfohlen)**
```bash
git clone https://github.com/SunnyCueq/cachyos-multi-updater.git
cd cachyos-multi-updater
```

**Option B: Als ZIP herunterladen**
1. Gehe zu https://github.com/benjarogit/sc-cachyos-multi-updater
2. Klicke auf "Code" → "Download ZIP"
3. Entpacke und navigiere zum Ordner

### Schritt 2: Setup ausführen

Der einfachste Weg zum Starten:

```bash
./cachyos-update
```

Wähle Option `1` um das Setup-Script auszuführen, das:
- Dich durch die Konfiguration führt
- Eine Desktop-Verknüpfung erstellt (optional)
- Das Update-Script automatisch startet

**Alternative: Manuelle Einrichtung**
```bash
cd cachyos-multi-updater
chmod +x update-all.sh
./update-all.sh --help  # Teste ob es funktioniert
```

### Schritt 3: Konfigurieren (optional)

Erstelle Konfigurationsdatei:
```bash
cp cachyos-multi-updater/config.conf.example cachyos-multi-updater/config.conf
nano cachyos-multi-updater/config.conf
```

Siehe [Konfiguration](#-konfiguration) Abschnitt unten für Details.

---

## 💻 Wie man es verwendet

### Console-Version

**Mit Menü starten:**
```bash
./cachyos-update
```

Zeigt ein Menü mit Optionen:
1. Setup durchführen (Erstinstallation)
2. Updates starten (Updates starten)
3. Beenden (Beenden)

**Direkte Script-Ausführung:**
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

### GUI-Version

**GUI starten:**
```bash
./cachyos-update-gui
```

Die GUI bietet eine moderne, benutzerfreundliche Oberfläche zur Verwaltung von System-Updates ohne Kommandozeile.

#### GUI-Features

**Hauptfenster:**
- **Komponenten-Auswahl** - Checkboxen zum Aktivieren/Deaktivieren jedes Update-Typs (System, AUR, Cursor, AdGuard, Flatpak)
- **Echtzeit-Ausgabe** - Farbige Konsolen-Ausgabe mit Update-Fortschritt:
  - 🟢 Grün: Erfolgsmeldungen
  - 🔴 Rot: Fehlermeldungen
  - 🟠 Orange: Warnmeldungen
  - ⚫ Schwarz: Normale Ausgabe
- **Fortschrittsbalken** - Visueller Fortschrittsindikator (0-100%)
- **Status-Anzeige** - Aktuelle Statusmeldung und Update-Informationen
- **Versionsprüfung** - Automatische Prüfung auf Script-Updates (zeigt an, ob neuere Version verfügbar)
- **Theme-Unterstützung** - Helles und dunkles Theme (folgt System-Theme)

**Buttons:**
- **Updates prüfen** - Führt Update-Script im Dry-Run-Modus aus (nur Vorschau, keine Änderungen)
- **Updates starten** - Startet den tatsächlichen Update-Prozess
- **Stoppen** - Stoppt einen laufenden Update (falls möglich)
- **Einstellungen** - Öffnet umfassenden Einstellungs-Dialog
- **Logs anzeigen** - Öffnet Log-Viewer zum Durchsuchen von Update-Logs

**Einstellungs-Dialog (6 Tabs):**

1. **Update-Komponenten** - Jede Update-Komponente aktivieren/deaktivieren
2. **Allgemeine Einstellungen** - Log-Dateien, Wiederholungen, Benachrichtigungen, Farben, Dry-Run-Modus
3. **Logs** - Log-Dateien direkt in der GUI anzeigen und durchsuchen
4. **System** - Script-Pfade, Verzeichnisse, Spracheinstellungen
5. **Erweiterte Einstellungen** - GitHub-Repository, Pfade, Verzeichnisse, GUI-Sprache
6. **Info** - Versionsinformationen, Links zu GitHub, Changelog

**Zusätzliche Features:**
- **Sichere Passwort-Verwaltung** - Verschlüsselte Sudo-Passwort-Speicherung (System-Keyring oder Fernet-Verschlüsselung)
- **Desktop-Verknüpfung erstellen** - Desktop-Verknüpfungen direkt aus der GUI erstellen
- **Update-Statistiken** - Update-Historie und Erfolgsraten anzeigen
- **Log-Viewer** - Log-Dateien mit korrekter Formatierung durchsuchen und anzeigen
- **Toast-Benachrichtigungen** - Desktop-Benachrichtigungen bei Update-Abschluss
- **Syntax-Hervorhebung** - Farbige Ausgabe im Konsolen-Bereich für bessere Lesbarkeit
- **Animationen** - Sanfte UI-Animationen und Übergänge
- **Internationalisierung** - Mehrsprachige Unterstützung (Deutsch/Englisch, automatisch erkannt)

**Voraussetzungen:**
- PyQt6 muss installiert sein: `pip3 install PyQt6`
- Oder alle Abhängigkeiten installieren: `pip3 install -r cachyos-multi-updater/requirements-gui.txt`

**GUI-Installation:**
```bash
# PyQt6 installieren
pip3 install PyQt6

# Oder alle GUI-Abhängigkeiten installieren
pip3 install -r cachyos-multi-updater/requirements-gui.txt

# Optional: Für sichere Passwort-Speicherung installieren
pip3 install keyring cryptography
```

**GUI-Verwendung:**
1. GUI starten: `./cachyos-update-gui`
2. Auswählen welche Komponenten aktualisiert werden sollen (Checkboxen)
3. "Updates prüfen" klicken um Änderungen vorzuschauen (Dry-Run)
4. "Updates starten" klicken um den Update-Prozess zu beginnen
5. Fortschritt in Echtzeit überwachen
6. Logs anzeigen falls nötig
7. Einstellungen über den Einstellungen-Button konfigurieren

**GUI-Vorteile:**
- ✅ Keine Kommandozeilen-Kenntnisse erforderlich
- ✅ Visuelles Feedback und Fortschrittsanzeige
- ✅ Einfache Konfiguration über Einstellungs-Dialog
- ✅ Sichere Passwort-Verwaltung
- ✅ Echtzeit-Update-Überwachung
- ✅ Log-Anzeige ohne Terminal
- ✅ Desktop-Benachrichtigungen
- ✅ Moderne, intuitive Oberfläche

---

## ⚙️ Konfiguration

Das Script kann über `cachyos-multi-updater/config.conf` angepasst werden. Kopiere von `config.conf.example` und bearbeite nach Bedarf.

### Konfigurations-Optionen

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
| `ENABLE_AUTO_UPDATE` | `true`/`false` | `false` | Automatische Script-Updates aktivieren |

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

# Downloads
DOWNLOAD_RETRIES=3
```

### Konfigurations-Priorität

1. **Befehlszeilen-Optionen** (höchste Priorität)
2. **Konfigurationsdatei** (`config.conf`)
3. **Standardwerte** (niedrigste Priorität)

---

## 🐛 Fehlerbehebung

### Häufige Probleme

#### Script sagt "Update läuft bereits!" (Update läuft bereits)

**Lösung:** Lösche die Lock-Datei:
```bash
rm cachyos-multi-updater/.update-all.lock
```

**Warum:** Das Script könnte abgestürzt oder unterbrochen worden sein und die Lock-Datei zurückgelassen haben.

#### "Permission denied" beim Ausführen des Scripts

**Lösung:** Mache es ausführbar:
```bash
chmod +x cachyos-update
chmod +x cachyos-update-gui
chmod +x cachyos-multi-updater/update-all.sh
```

#### "Command not found" für yay/paru

**Lösung:** Installiere einen AUR-Helper oder deaktiviere AUR-Updates:
```bash
# yay installieren
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si

# Oder in config.conf deaktivieren
ENABLE_AUR_UPDATE=false
```

#### Cursor wird nicht aktualisiert

**Prüfen:**
1. Cursor installiert? `which cursor`
2. Internetverbindung? `ping api2.cursor.sh`
3. Logs prüfen: `grep -i cursor cachyos-multi-updater/logs/update-*.log`
4. Deaktivieren falls nicht benötigt: `ENABLE_CURSOR_UPDATE=false`

#### AdGuard Home wird nicht aktualisiert

**Prüfen:**
1. Installiert in `~/AdGuardHome`? `ls -l ~/AdGuardHome/AdGuardHome`
2. Logs prüfen: `grep -i adguard cachyos-multi-updater/logs/update-*.log`
3. Deaktivieren falls nicht benötigt: `ENABLE_ADGUARD_UPDATE=false`

#### Script läuft aber nichts passiert

**Mögliche Ursachen:**
1. Alles ist bereits aktuell (normal!)
2. Dry-Run-Modus aktiviert (`DRY_RUN=true` in config)
3. Alle Updates in config deaktiviert
4. Logs prüfen: `cat cachyos-multi-updater/logs/$(ls -t cachyos-multi-updater/logs/ | head -1)`

#### GUI startet nicht

**Prüfen:**
1. PyQt6 installiert? `python3 -c "from PyQt6.QtWidgets import QApplication"`
2. Python-Version 3.8+? `python3 --version`
3. Abhängigkeiten installiert? `pip3 install -r cachyos-multi-updater/requirements-gui.txt`
4. Script-Verzeichnis korrekt? Prüfe dass `cachyos-multi-updater/update-all.sh` existiert

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

#### GUI Passwort-Dialog funktioniert nicht

**Prüfen:**
1. Keyring installiert? `pip3 install keyring cryptography`
2. System-Keyring verfügbar? (normalerweise automatisch)
3. Versuche Passwort jedes Mal manuell einzugeben (Passwort-Speicherung deaktivieren)

**Lösung:**
```bash
# Passwort-Speicher-Abhängigkeiten installieren
pip3 install keyring cryptography
```

### Hilfe erhalten

1. **Logs zuerst prüfen** - Die meisten Probleme sind in `cachyos-multi-updater/logs/` geloggt
2. **Dry-Run-Modus versuchen** - Siehe was passieren würde: `./cachyos-multi-updater/update-all.sh --dry-run`
3. **Fehlerbehebungs-Abschnitt prüfen** - Dein Problem könnte oben aufgeführt sein
4. **GitHub-Issue erstellen** - Füge Log-Ausschnitte hinzu und beschreibe was du versucht hast

---

## 📚 Weitere Informationen

### Logs

Logs werden in `cachyos-multi-updater/logs/` gespeichert mit Namen wie `update-20241215-143022.log`.

**Logs anzeigen:**
```bash
# Alle Logs auflisten
ls -lh cachyos-multi-updater/logs/

# Neuestes Log anzeigen
cat cachyos-multi-updater/logs/$(ls -t cachyos-multi-updater/logs/ | head -1)

# Nach Fehlern suchen
grep -i error cachyos-multi-updater/logs/update-*.log
```

### Statistiken

Update-Statistiken anzeigen:
```bash
./cachyos-multi-updater/update-all.sh --stats
```

Zeigt:
- Gesamtanzahl der Updates
- Erfolgreiche vs. fehlgeschlagene Updates
- Erfolgsrate in Prozent
- Durchschnittliche Update-Dauer
- Zeitstempel des letzten Updates

### Desktop-Verknüpfung

Das Setup-Script kann eine Desktop-Verknüpfung erstellen. Oder manuell erstellen:

```bash
cd cachyos-multi-updater
./create-desktop-shortcut.sh
```

### Script aktualisieren

Wenn du mit Git geklont hast:
```bash
cd cachyos-multi-updater
git pull
```

---

## ❓ FAQ

### Q: Wie oft sollte ich dieses Script ausführen?

**A:** Das hängt von deiner Präferenz ab:
- Täglich (für Sicherheits-Updates)
- Wöchentlich (ausgewogener Ansatz)
- Vor wichtigen Arbeitssitzungen
- Bei Benachrichtigungen über Updates

### Q: Ist es sicher, es automatisch (via cron) auszuführen?

**A:** Ja, aber mit Vorsicht:
- Das Script hat Fehlerbehandlung
- Benötigt sudo-Zugriff (richtig konfigurieren)
- Zuerst manuell testen
- Erwäge `--dry-run` in cron zu verwenden

### Q: Kann ich das auf normalem Arch Linux verwenden?

**A:** Ja! Obwohl für CachyOS entwickelt, funktioniert es auch auf Arch Linux.

### Q: Schließt und startet das Script Cursor automatisch neu?

**A:** Nein, das Script schließt oder startet Cursor NICHT automatisch neu. Es lädt und installiert nur das Update. Du kannst Cursor manuell neu starten falls nötig.

### Q: Wird dieses Script mein System kaputt machen?

**A:** Das Script ist darauf ausgelegt, sicher zu sein:
- Verwendet Standard-Paketmanager
- Hat Fehlerbehandlung
- Erstellt Backup der AdGuard Home-Konfiguration
- Loggt alles

Jedoch trägt jedes System-Update ein gewisses Risiko. Verwende zuerst `--dry-run` wenn du unsicher bist!

### Q: Kann ich anpassen, was aktualisiert wird?

**A:** Ja! Mehrere Möglichkeiten:
1. **Konfigurationsdatei** (`config.conf`) - Komponenten aktivieren/deaktivieren
2. **Befehlszeilen-Flags** - `--only-system`, `--only-aur`, etc.
3. **Beides kombinieren** - Config für Standardwerte, Flags für einmalige Änderungen

---

## 📅 Versionshistorie

Für die vollständige Versionshistorie und Changelog siehe [GitHub Releases](https://github.com/SunnyCueq/cachyos-multi-updater/releases).

---

## 📄 Lizenz

Dieses Projekt ist Open Source. Du kannst es frei verwenden, modifizieren und unter den Bedingungen der MIT-Lizenz verteilen.

## 🤝 Beitragen

Verbesserungen und Fehlerberichte sind willkommen! Bitte erstelle ein Issue oder Pull Request auf [GitHub](https://github.com/benjarogit/sc-cachyos-multi-updater).

## 📧 Support

Bei Fragen oder Problemen:
1. Prüfe die Log-Dateien in `cachyos-multi-updater/logs/`
2. Prüfe den [Fehlerbehebungs](#-fehlerbehebung) Abschnitt oben
3. Erstelle ein Issue auf [GitHub](https://github.com/benjarogit/sc-cachyos-multi-updater)

## 🔗 Links

- **GitHub Repository:** https://github.com/benjarogit/sc-cachyos-multi-updater
- **Issues:** https://github.com/benjarogit/sc-cachyos-multi-updater/issues

---

**Viel Erfolg mit deinen Updates! 🎉**
