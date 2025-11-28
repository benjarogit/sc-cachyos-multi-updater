# CachyOS Multi-Updater

> **Sprache / Language:** [🇩🇪 Deutsch](README.de.md) | [🇬🇧 English](README.md)

Ein einfaches One-Click-Update-Tool für CachyOS, das automatisch System-Pakete, AUR-Pakete, den Cursor Editor, Flatpak-Anwendungen und AdGuard Home aktualisiert.

---

## 📖 Inhaltsverzeichnis

1. [Was ist das?](#-was-ist-das)
2. [Was macht dieses Script?](#-was-macht-dieses-script)
3. [Was du zuerst wissen musst](#-was-du-zuerst-wissen-musst)
4. [Voraussetzungen](#-voraussetzungen)
5. [Installationsanleitung](#-installationsanleitung)
6. [Wie man es verwendet](#-wie-man-es-verwendet)
7. [Konfiguration im Detail erklärt](#-konfiguration-im-detail-erklärt)
8. [Logs verstehen](#-logs-verstehen)
9. [Fehlerbehebung](#-fehlerbehebung)
10. [FAQ](#-faq-häufig-gestellte-fragen)
11. [Versionshistorie](#-versionshistorie)

---

## 🤔 Was ist das?

**CachyOS Multi-Updater** ist ein Script (ein kleines Programm), das dir hilft, dein CachyOS Linux-System auf dem neuesten Stand zu halten. Anstatt verschiedene Teile deines Systems manuell nacheinander zu aktualisieren, macht dieses Script alles automatisch in einem Durchgang.

### Was ist CachyOS?

CachyOS ist ein Linux-Betriebssystem, das auf Arch Linux basiert. Es ist darauf ausgelegt, schnell und für Performance optimiert zu sein. Wie jedes Betriebssystem benötigt es regelmäßige Updates, um Sicherheitskorrekturen, neue Features und Fehlerbehebungen zu erhalten.

### Warum brauche ich das?

Normalerweise erfordert das Aktualisieren eines Linux-Systems das Ausführen mehrerer Befehle:
- System-Pakete aktualisieren
- AUR-Pakete aktualisieren (Community-Erstellte Software)
- Anwendungen wie den Cursor Editor aktualisieren
- Dienste wie AdGuard Home aktualisieren

Dieses Script macht all das automatisch und spart dir Zeit, während es sicherstellt, dass alles aktuell bleibt.

---

## 🚀 Was macht dieses Script?

Dieses Script aktualisiert automatisch fünf verschiedene Dinge auf deinem System und bereinigt anschließend:

### 1. ✅ CachyOS System-Updates (via pacman)

**Was ist pacman?** Pacman ist der Paketmanager für Arch Linux und CachyOS. Es ist wie ein App-Store, der alle Software auf deinem System verwaltet.

**Was wird aktualisiert?** Alle offiziellen CachyOS-Pakete, einschließlich:
- System-Bibliotheken
- Anwendungen aus den offiziellen Repositories
- Sicherheits-Patches
- Fehlerbehebungen

**Wie funktioniert es:** Das Script führt `sudo pacman -Syu` aus, was bedeutet:
- `-S` = Sync (Pakete aktualisieren)
- `-y` = Paketdatenbank aktualisieren
- `-u` = Alle Pakete upgraden
- `--noconfirm` = Keine Bestätigung anfordern (automatisch)

### 2. ✅ AUR-Pakete (via yay oder paru)

**Was ist AUR?** AUR steht für "Arch User Repository". Es ist ein Community-gesteuertes Repository, in dem Benutzer Pakete teilen, die nicht in den offiziellen Repositories sind. Stell es dir als einen Community-App-Store vor.

**Was ist yay/paru?** Das sind "AUR-Helper" - Tools, die das Installieren und Aktualisieren von AUR-Paketen erleichtern. Du brauchst eines davon installiert, damit diese Funktion funktioniert.

**Was wird aktualisiert?** Alle Pakete, die du von AUR installiert hast, wie z.B.:
- Community-erstellte Anwendungen
- Custom-Builds von Software
- Pakete, die nicht in offiziellen Repos verfügbar sind

**Wie funktioniert es:** Das Script erkennt automatisch, ob du `yay` oder `paru` installiert hast und verwendet es, um alle AUR-Pakete zu aktualisieren.

### 3. ✅ Cursor Editor (automatischer Download und Update)

**Was ist Cursor?** Cursor ist ein Code-Editor (wie VS Code) mit KI-Features. Wenn du es installiert hast, hält dieses Script es auf dem neuesten Stand.

**Was passiert während des Updates?**
1. Das Script prüft deine aktuelle Cursor-Version (aus package.json)
2. Prüft die neueste verfügbare Version via HTTP HEAD Request (kein Download nötig!)
3. Extrahiert die Version aus dem Location-Header (`cursor_2.0.69_amd64.deb` → `2.0.69`)
4. Vergleicht Versionen - wenn bereits aktuell, überspringt Download und Installation komplett
5. Wenn Update nötig, lädt und installiert die neue Version
6. Die .deb-Datei wird automatisch nach der Installation gelöscht
7. Du kannst Cursor manuell neu starten, falls es gelaufen ist

**Hinweis:** Die Versionsprüfung nutzt einen HTTP HEAD Request (nur wenige KB) statt die gesamte .deb-Datei (132MB) herunterzuladen. Das macht die Prüfung deutlich schneller und spart Bandbreite. Falls der HTTP HEAD Request fehlschlägt, nutzt das Script die alte Methode (Download + Extraktion) als Fallback.

**Hinweis:** Das Script schließt oder startet Cursor NICHT automatisch. Falls Cursor läuft, solltest du es manuell schließen, bevor du das Update ausführst, für eine saubere Installation.

**Hinweis:** Falls Cursor über CachyOS-Repositories aktualisiert wird, kannst du diese Funktion in der Konfiguration deaktivieren.

### 4. ✅ Flatpak-Anwendungen (automatisches Update)

**Was ist Flatpak?** Flatpak ist ein universelles Paketformat für Linux, das es Anwendungen ermöglicht, auf jeder Linux-Distribution zu laufen. Viele moderne Anwendungen werden als Flatpak-Pakete verteilt.

**Was wird aktualisiert?** Alle Flatpak-Anwendungen, die auf deinem System installiert sind, wie z.B.:
- Desktop-Anwendungen (z.B. Firefox, LibreOffice, GIMP)
- Entwicklungstools
- Media-Player
- Spiele
- Alle anderen Flatpak-Anwendungen, die du installiert hast

**Wie funktioniert es:** Das Script führt `flatpak update -y` aus, was bedeutet:
- Prüft auf verfügbare Updates für alle installierten Flatpak-Anwendungen
- Lädt und installiert Updates automatisch
- Aktualisiert nur, wenn Updates verfügbar sind (überspringt, wenn bereits aktuell)

**Hinweis:** Flatpak muss auf deinem System installiert sein, damit diese Funktion funktioniert. Falls Flatpak nicht installiert ist, überspringt das Script Flatpak-Updates mit einer Warnung.

### 5. ✅ AdGuard Home (automatischer Download und Update)

**Was ist AdGuard Home?** AdGuard Home ist ein netzwerkweiter Werbeblocker und DNS-Server. Es blockiert Werbung und Tracker für alle Geräte in deinem Netzwerk.

**Was passiert während des Updates?**
1. Prüft aktuelle Version
2. Prüft neueste Version über GitHub Releases API
3. Wenn bereits aktuell, überspringt Download
4. Wenn Update nötig:
   - Stoppt den AdGuard Home-Service
   - Lädt die neueste Version von offiziellen AdGuard-Servern herunter
   - Erstellt ein Backup deiner Konfiguration
   - Installiert die neue Version
   - Startet den Service neu

**Wichtig:** AdGuard Home muss in `~/AdGuardHome` (in deinem Home-Verzeichnis) installiert sein.

### 6. ✅ Automatische Bereinigung (nach Updates)

**Was ist Bereinigung?** Nachdem alle Updates abgeschlossen sind, bereinigt das Script automatisch temporäre Dateien, alte Pakete und nicht verwendete Abhängigkeiten, um dein System sauber zu halten und Speicherplatz zu sparen.

**Was wird bereinigt?**
- **Pacman-Cache:** Entfernt alte und deinstallierte Pakete (behält letzte 3 Versionen)
- **Orphan-Pakete:** Entfernt Pakete, die nicht mehr benötigt werden
- **Flatpak-Cache:** Entfernt nicht verwendete Flatpak-Laufzeiten und -Anwendungen
- **Cursor-Downloads:** Entfernt verbleibende `.deb`-Dateien aus dem Script-Verzeichnis
- **AdGuard temporäre Dateien:** Bereinigt temporäre Verzeichnisse in `/tmp`
- **Cursor temporäre Dateien:** Bereinigt Extraktions-Verzeichnisse in `/tmp`

**Wie funktioniert es:** Die Bereinigung läuft automatisch nach Abschluss aller Updates. Keine Benutzerinteraktion erforderlich.

---

## 📚 Was du zuerst wissen musst

### Grundlegende Linux-Konzepte

**Terminal/Kommandozeile:** Das ist eine textbasierte Oberfläche, in der du Befehle eingibst. Auf CachyOS kannst du es öffnen, indem du `Strg+Alt+T` drückst oder nach "Terminal" im Anwendungsmenü suchst.

**sudo:** Das steht für "Super User DO". Es erlaubt dir, Befehle mit Administratorrechten auszuführen. Du musst dein Passwort eingeben, wenn das Script danach fragt.

**Script:** Ein Script ist eine Datei, die Befehle enthält, die der Computer ausführen kann. Dieses Projekt ist ein Bash-Script (geschrieben in der Bash-Programmiersprache).

**Repository:** Eine Sammlung von Software-Paketen. Stell es dir als eine Bibliothek von Programmen vor, die du installieren kannst.

### Dateipfade erklärt

Wenn du Pfade wie `/home/benutzername/` siehst, bedeutet das:
- `/` = Die Wurzel deines Dateisystems (wie C:\ unter Windows)
- `/home/benutzername/` = Dein Home-Verzeichnis (wie der Ordner Dokumente)
- `~` = Kurzform für dein Home-Verzeichnis
- `./` = Aktuelles Verzeichnis (wo du gerade bist)

---

## 📋 Voraussetzungen

Bevor du dieses Script verwenden kannst, brauchst du:

### Erforderlich (muss vorhanden sein):

1. **CachyOS oder Arch Linux** - Dieses Script ist für diese Systeme entwickelt
   - Wie prüfen: Terminal öffnen und `cat /etc/os-release` eingeben
   - Du solltest "CachyOS" oder "Arch Linux" sehen

2. **sudo-Berechtigungen** - Du musst Befehle als Administrator ausführen können
   - Wie prüfen: `sudo -v` im Terminal eingeben
   - Wenn es nach deinem Passwort fragt, hast du sudo-Zugriff

3. **Internetverbindung** - Das Script braucht Internet, um Updates herunterzuladen

### Optional (nice to have):

4. **AUR-Helper (yay oder paru)** - Nur nötig, wenn du AUR-Pakete aktualisieren möchtest
   - Wie prüfen: `which yay` oder `which paru` im Terminal eingeben
   - Wenn es einen Pfad zeigt, ist es installiert
   - Wenn nicht, kannst du es installieren (siehe Fehlerbehebung)

5. **Cursor Editor** - Nur nötig, wenn du Cursor aktualisieren möchtest
   - Wie prüfen: `which cursor` im Terminal eingeben
   - Wenn es einen Pfad zeigt, ist Cursor installiert
   - **Hinweis:** Falls Cursor über CachyOS-Repositories aktualisiert wird, kannst du diese Funktion deaktivieren

6. **AdGuard Home** - Nur nötig, wenn du AdGuard Home aktualisieren möchtest
   - Wie prüfen: Nach der Datei `~/AdGuardHome/AdGuardHome` suchen
   - `ls ~/AdGuardHome/AdGuardHome` im Terminal eingeben

---

## 🔧 Installationsanleitung

Dies ist eine Schritt-für-Schritt-Anleitung für komplette Anfänger. Folge jedem Schritt sorgfältig.

### Schritt 1: Script herunterladen

Du hast zwei Optionen:

#### Option A: Mit Git (empfohlen)

**Was ist Git?** Git ist ein Versionskontrollsystem. Es ist eine Möglichkeit, Software herunterzuladen und aktuell zu halten.

1. Öffne ein Terminal (drücke `Strg+Alt+T` oder suche nach "Terminal")
2. Navigiere zu dem Ort, wo du das Script installieren möchtest (z.B. dein Home-Verzeichnis):
   ```bash
   cd ~
   ```
3. Klone das Repository (lade die Dateien herunter):
   ```bash
   git clone https://github.com/SunnyCueq/cachyos-multi-updater.git
   ```
   Dies erstellt einen Ordner namens `cachyos-multi-updater` mit allen Dateien.

4. Betrete den Ordner:
   ```bash
   cd cachyos-multi-updater
   ```

#### Option B: Als ZIP herunterladen

1. Gehe zu https://github.com/SunnyCueq/cachyos-multi-updater
2. Klicke auf den grünen "Code"-Button
3. Klicke auf "Download ZIP"
4. Entpacke die ZIP-Datei an einen Ort (z.B. `~/Downloads/`)
5. Öffne Terminal und navigiere zum entpackten Ordner:
   ```bash
   cd ~/Downloads/cachyos-multi-updater-main
   ```

### Schritt 2: Setup-Script ausführen (empfohlen für Erstinstallation)

**Der einfachste Weg zum Starten!** Das Setup-Script führt dich durch die Konfiguration.

1. Setup-Script ausführbar machen:
   ```bash
   chmod +x setup.sh
   ```

2. Setup-Script ausführen:
   ```bash
   ./setup.sh
   ```

3. Das Setup-Script wird:
   - Nach Update-Modus fragen (--dry-run, --interactive oder automatisch)
   - Fragen ob Desktop-Verknüpfung erstellt werden soll
   - Desktop-Verknüpfung mit gewählten Optionen erstellen
   - Update-Script automatisch starten

**Alternative: Manuelle Einrichtung**

Falls du es lieber manuell einrichten möchtest:

1. Script ausführbar machen:
   ```bash
   chmod +x update-all.sh
   ```

2. Überprüfe ob es funktioniert hat:
   ```bash
   ls -l update-all.sh
   ```
   Du solltest etwas wie `-rwxr-xr-x` sehen - das `x` bedeutet, dass es ausführbar ist.

**Was wenn ich "Permission denied" bekomme?**
- Stelle sicher, dass du im richtigen Verzeichnis bist
- Versuche: `chmod 755 update-all.sh`
- Wenn es immer noch nicht funktioniert, musst du möglicherweise `sudo` verwenden (aber das ist ungewöhnlich)

### Schritt 3: Script testen (optional aber empfohlen)

Bevor du es wirklich verwendest, teste, ob es funktioniert:

1. Führe den Hilfe-Befehl aus:
   ```bash
   ./update-all.sh --help
   ```

2. Du solltest eine Hilfe-Nachricht sehen. Wenn du einen Fehler siehst, schaue in den Abschnitt Fehlerbehebung.

3. Versuche den Dry-Run-Modus (sicher, macht keine Änderungen):
   ```bash
   ./update-all.sh --dry-run
   ```

### Schritt 4: Desktop-Verknüpfung installieren (optional)

**Was ist eine Desktop-Verknüpfung?** Es ist ein Icon im Anwendungsmenü (und optional auf deinem Desktop), auf das du klicken kannst, um das Script auszuführen, ohne Terminal zu öffnen.

#### Option A: Anwendungsmenü-Icon (Empfohlen)

Dies erstellt ein Icon im Anwendungsmenü:

1. Kopiere die Desktop-Datei in deinen Anwendungsordner:
   ```bash
   cp update-all.desktop ~/.local/share/applications/
   ```

2. Bearbeite die Desktop-Datei, um den korrekten Pfad zu setzen:
   ```bash
   nano ~/.local/share/applications/update-all.desktop
   ```

3. Finde die Zeile, die sagt:
   ```ini
   Exec=bash -c "cd '%k' && ./update-all.sh"
   ```

4. Ersetze sie mit dem tatsächlichen Pfad zu deinem Script. Zum Beispiel, wenn du es in deinem Home-Verzeichnis installiert hast:
   ```ini
   Exec=bash -c "cd '/home/deinbenutzername/cachyos-multi-updater' && ./update-all.sh"
   ```
   **Wichtig:** Ersetze `deinbenutzername` mit deinem tatsächlichen Benutzernamen!

5. Speichere und beende:
   - Drücke `Strg+O` zum Speichern
   - Drücke `Enter` zum Bestätigen
   - Drücke `Strg+X` zum Beenden

6. Mache die Desktop-Datei ausführbar:
   ```bash
   chmod +x ~/.local/share/applications/update-all.desktop
   ```

7. Teste es:
   - Öffne dein Anwendungsmenü (normalerweise durch Drücken der Super/Windows-Taste)
   - Suche nach "Update All"
   - Klicke darauf
   - Ein Terminal sollte sich öffnen und das Script sollte starten

#### Option B: Desktop-Icon (Sichtbar auf dem Desktop)

Um das Icon direkt auf deinem Desktop anzuzeigen:

1. Folge den Schritten 1-6 von Option A oben

2. Kopiere die Desktop-Datei auf deinen Desktop:
   ```bash
   cp ~/.local/share/applications/update-all.desktop ~/Desktop/
   ```
   Oder wenn dein Desktop an einem anderen Ort ist:
   ```bash
   cp ~/.local/share/applications/update-all.desktop ~/Schreibtisch/  # Deutsch
   cp ~/.local/share/applications/update-all.desktop ~/Desktop/        # Englisch
   ```

3. Mache es ausführbar:
   ```bash
   chmod +x ~/Desktop/update-all.desktop
   ```

4. Das Icon sollte jetzt auf deinem Desktop erscheinen. Du kannst darauf doppelklicken, um das Script auszuführen.

**Hinweis:** Einige Desktop-Umgebungen erfordern möglicherweise, dass du "Anwendungen starten erlauben" in den Desktop-Einstellungen aktivierst, damit Icons funktionieren.

#### Icon ändern

Die Desktop-Datei verwendet standardmäßig ein System-Icon (`system-software-update`). Um es zu ändern:

1. Öffne die Desktop-Datei:
   ```bash
   nano ~/.local/share/applications/update-all.desktop
   ```

2. Finde die Zeile:
   ```ini
   Icon=system-software-update
   ```

3. Ersetze sie mit einer dieser Optionen:

   **Option 1: System-Icon-Name verwenden**
   ```ini
   Icon=system-software-update
   Icon=system-update
   Icon=software-update-available
   Icon=update-manager
   ```
   (Häufige Icon-Namen auf Linux-Systemen)

   **Option 2: Benutzerdefinierte Icon-Datei verwenden**
   ```ini
   Icon=/pfad/zum/deinem/icon.png
   ```
   Zum Beispiel:
   ```ini
   Icon=/home/deinbenutzername/Bilder/mein-update-icon.png
   ```

   **Option 3: Icon aus dem Script-Verzeichnis verwenden**
   ```ini
   Icon=/home/deinbenutzername/cachyos-multi-updater/icon.png
   ```

4. Speichere und beende (Strg+O, Enter, Strg+X)

5. Aktualisiere den Desktop (oder melde dich ab und wieder an), um das neue Icon zu sehen

**Wie finde ich meinen Benutzernamen?**
- Tippe `whoami` im Terminal
- Oder tippe `echo $USER`

**Wie finde ich den vollständigen Pfad zum Script?**
- Navigiere zum Script-Ordner im Terminal
- Tippe `pwd` (print working directory)
- Dies zeigt den vollständigen Pfad

### Schritt 5: Konfigurieren (optional, aber empfohlen)

**Was ist Konfiguration?** Konfiguration lässt dich anpassen, wie sich das Script verhält. Du kannst bestimmte Updates aktivieren/deaktivieren, Einstellungen ändern, etc.

Siehe den Abschnitt [Konfiguration im Detail erklärt](#-konfiguration-im-detail-erklärt) unten für vollständige Anweisungen.

---

## 💻 Wie man es verwendet

### Methode 1: Desktop-Verknüpfung verwenden

Dies ist die einfachste Methode, wenn du die Desktop-Verknüpfung eingerichtet hast:

1. Öffne dein Anwendungsmenü (normalerweise durch Drücken der Super/Windows-Taste)
2. Tippe "Update All" in das Suchfeld
3. Klicke auf "Update All"
4. Ein Terminal-Fenster öffnet sich
5. Das Script startet automatisch
6. Wenn es nach deinem Passwort fragt, tippe es ein und drücke Enter
   - **Hinweis:** Beim Tippen deines Passworts siehst du keine Zeichen (nicht einmal Punkte). Das ist normal aus Sicherheitsgründen.
7. Warte, bis die Updates abgeschlossen sind
8. Das Terminal zeigt dir, was aktualisiert wird

### Methode 2: Kommandozeile verwenden

Diese Methode erfordert, dass du Terminal manuell öffnest:

1. Öffne Terminal (drücke `Strg+Alt+T` oder suche nach "Terminal")
2. Navigiere zum Script-Ordner:
   ```bash
   cd ~/cachyos-multi-updater
   ```
   (Passe den Pfad an, wenn du es woanders installiert hast)

3. Führe das Script aus:
   ```bash
   ./update-all.sh
   ```

4. Gib dein Passwort ein, wenn danach gefragt wird

5. Warte, bis die Updates abgeschlossen sind

### Kommandozeilen-Optionen erklärt

Das Script unterstützt mehrere Optionen, die sein Verhalten ändern:

#### Standard-Update (alle Komponenten)

```bash
./update-all.sh
```

Dies aktualisiert alles: System-Pakete, AUR-Pakete, Cursor, Flatpak-Anwendungen und AdGuard Home.

#### Selektive Updates

Manchmal möchtest du nur bestimmte Dinge aktualisieren:

**Nur System-Updates:**
```bash
./update-all.sh --only-system
```
Dies aktualisiert nur CachyOS System-Pakete. Nützlich, wenn du nur offizielle Pakete aktualisieren möchtest.

**Nur AUR-Pakete:**
```bash
./update-all.sh --only-aur
```
Dies aktualisiert nur Pakete von AUR. Nützlich, wenn du nur Community-Pakete aktualisieren möchtest.

**Nur Cursor:**
```bash
./update-all.sh --only-cursor
```
Dies aktualisiert nur den Cursor Editor. Nützlich, wenn du nur Cursor aktualisieren möchtest, ohne etwas anderes anzufassen.

**Nur AdGuard Home:**
```bash
./update-all.sh --only-adguard
```
Dies aktualisiert nur AdGuard Home. Nützlich, wenn du nur AdGuard aktualisieren möchtest, ohne andere Updates.

**Nur Flatpak:**
```bash
./update-all.sh --only-flatpak
```
Dies aktualisiert nur Flatpak-Anwendungen. Nützlich, wenn du nur Flatpak-Apps aktualisieren möchtest, ohne andere Updates.

**Warum selektive Updates verwenden?**
- Schneller (aktualisiert nur was du brauchst)
- Sicherer (weniger Chance, dass etwas kaputt geht)
- Mehr Kontrolle (du entscheidest, was aktualisiert wird)

#### Dry-Run Modus (Vorschau ohne Änderungen)

```bash
./update-all.sh --dry-run
```

**Was ist Dry-Run?** Dry-Run zeigt dir, was aktualisiert WÜRDE, ohne tatsächlich Änderungen vorzunehmen. Es ist wie eine Vorschau.

**Wann verwenden:**
- Beim ersten Mal mit dem Script (um zu sehen, was es macht)
- Vor einem großen Update (um zu sehen, was sich ändern wird)
- Zum Testen (um sicherzustellen, dass alles funktioniert)

**Was du sehen wirst:**
- Eine Liste dessen, was aktualisiert würde
- Aktuelle Versionen
- Welche Befehle ausgeführt würden
- Aber KEINE tatsächlichen Änderungen werden vorgenommen

#### Version anzeigen

```bash
./update-all.sh --version
```
oder
```bash
./update-all.sh -v
```

Dies zeigt die aktuelle Version des Scripts. Nützlich, um zu wissen, welche Version du verwendest.

#### Hilfe anzeigen

```bash
./update-all.sh --help
```
oder
```bash
./update-all.sh -h
```

Dies zeigt alle verfügbaren Optionen und wie man sie verwendet.

### Optionen kombinieren

Du kannst einige Optionen kombinieren:

```bash
./update-all.sh --only-system --dry-run
```

Dies würde zeigen, welche System-Updates durchgeführt würden, ohne sie tatsächlich durchzuführen.

---

## ⚙️ Konfiguration im Detail erklärt

Das Script kann mit einer Konfigurationsdatei angepasst werden. Dies ist optional - das Script funktioniert gut mit Standardeinstellungen. Aber Konfiguration gibt dir mehr Kontrolle.

### Was ist eine Konfigurationsdatei?

Eine Konfigurationsdatei (Config-Datei) ist eine Textdatei, die Einstellungen enthält. Das Script liest diese Datei und passt sein Verhalten basierend auf den Einstellungen an.

### Konfigurationsdatei erstellen

1. Navigiere zum Script-Ordner:
   ```bash
   cd ~/cachyos-multi-updater
   ```

2. Kopiere die Beispiel-Konfigurationsdatei:
   ```bash
   cp config.conf.example config.conf
   ```

3. Öffne sie in einem Texteditor:
   ```bash
   nano config.conf
   ```
   (Du kannst jeden Texteditor verwenden: `nano`, `vim`, `gedit`, `kate`, etc.)

4. Bearbeite die Werte nach Bedarf (siehe Erklärungen unten)

5. Speichere und beende:
   - In nano: `Strg+O` zum Speichern, `Enter` zum Bestätigen, `Strg+X` zum Beenden
   - In anderen Editoren: Verwende ihre Speicher-Funktion

### Format der Konfigurationsdatei

Die Konfigurationsdatei verwendet ein einfaches Format:
- Jede Einstellung steht in einer eigenen Zeile
- Format: `SCHLÜSSEL=wert`
- Zeilen, die mit `#` beginnen, sind Kommentare (werden ignoriert)
- Leere Zeilen werden ignoriert
- Groß-/Kleinschreibung spielt keine Rolle bei `true`/`false`-Werten

**Beispiel:**
```ini
# Dies ist ein Kommentar
ENABLE_SYSTEM_UPDATE=true
ENABLE_AUR_UPDATE=false
```

### Alle Konfigurationsoptionen erklärt

#### 1. ENABLE_SYSTEM_UPDATE

```ini
ENABLE_SYSTEM_UPDATE=true
```

**Was es macht:** Steuert, ob CachyOS System-Updates durchgeführt werden.

**Werte:**
- `true` = System-Updates sind aktiviert (Standard)
- `false` = System-Updates sind deaktiviert

**Wann deaktivieren:**
- Du möchtest nur AUR-Pakete aktualisieren
- Du testest und möchtest keine System-Änderungen
- Du bevorzugst es, System-Pakete manuell zu aktualisieren

**Beispiel:**
```ini
ENABLE_SYSTEM_UPDATE=false
```
Dies deaktiviert System-Updates. Nur AUR, Cursor und AdGuard würden aktualisiert.

#### 2. ENABLE_AUR_UPDATE

```ini
ENABLE_AUR_UPDATE=true
```

**Was es macht:** Steuert, ob AUR-Paket-Updates durchgeführt werden.

**Werte:**
- `true` = AUR-Updates sind aktiviert (Standard)
- `false` = AUR-Updates sind deaktiviert

**Wann deaktivieren:**
- Du hast yay/paru nicht installiert
- Du bevorzugst es, AUR-Pakete manuell zu aktualisieren
- Du möchtest nur System-Updates

**Beispiel:**
```ini
ENABLE_AUR_UPDATE=false
```
Dies deaktiviert AUR-Updates. Nur System-Pakete, Cursor und AdGuard würden aktualisiert.

#### 3. ENABLE_CURSOR_UPDATE

```ini
ENABLE_CURSOR_UPDATE=true
```

**Was es macht:** Steuert, ob der Cursor Editor aktualisiert wird.

**Werte:**
- `true` = Cursor-Updates sind aktiviert (Standard)
- `false` = Cursor-Updates sind deaktiviert

**Wann deaktivieren:**
- Du hast Cursor nicht installiert
- Du bevorzugst es, Cursor manuell zu aktualisieren
- Du möchtest nicht, dass Cursor während Updates geschlossen wird
- Cursor wird über CachyOS-Repositories aktualisiert (dann nicht nötig)

**Beispiel:**
```ini
ENABLE_CURSOR_UPDATE=false
```
Dies deaktiviert Cursor-Updates. Cursor wird vom Script nicht angefasst.

#### 4. ENABLE_FLATPAK_UPDATE

```ini
ENABLE_FLATPAK_UPDATE=true
```

**Was es macht:** Steuert, ob Flatpak-Anwendungen aktualisiert werden.

**Werte:**
- `true` = Flatpak-Updates sind aktiviert (Standard)
- `false` = Flatpak-Updates sind deaktiviert

**Wann deaktivieren:**
- Du hast Flatpak nicht installiert
- Du verwendest keine Flatpak-Anwendungen
- Du bevorzugst es, Flatpak-Anwendungen manuell zu aktualisieren

**Beispiel:**
```ini
ENABLE_FLATPAK_UPDATE=false
```
Dies deaktiviert Flatpak-Updates. Flatpak-Anwendungen werden vom Script nicht aktualisiert.

#### 5. ENABLE_ADGUARD_UPDATE

```ini
ENABLE_ADGUARD_UPDATE=true
```

**Was es macht:** Steuert, ob AdGuard Home aktualisiert wird.

**Werte:**
- `true` = AdGuard Home-Updates sind aktiviert (Standard)
- `false` = AdGuard Home-Updates sind deaktiviert

**Wann deaktivieren:**
- Du hast AdGuard Home nicht installiert
- Du bevorzugst es, AdGuard Home manuell zu aktualisieren
- Du möchtest nicht, dass der Service während Updates gestoppt wird

**Beispiel:**
```ini
ENABLE_ADGUARD_UPDATE=false
```
Dies deaktiviert AdGuard Home-Updates. AdGuard wird vom Script nicht angefasst.

#### 6. ENABLE_NOTIFICATIONS

```ini
ENABLE_NOTIFICATIONS=true
```

**Was es macht:** Steuert, ob Desktop-Benachrichtigungen angezeigt werden, wenn Updates abgeschlossen sind.

**Werte:**
- `true` = Benachrichtigungen sind aktiviert (Standard)
- `false` = Benachrichtigungen sind deaktiviert

**Was sind Desktop-Benachrichtigungen?** Das sind Pop-up-Nachrichten, die in der Ecke deines Bildschirms erscheinen. Sie zeigen an, wenn Updates fertig sind.

**Wann deaktivieren:**
- Du möchtest keine Pop-up-Benachrichtigungen
- Du führst das Script automatisch aus und brauchst keine Benachrichtigungen
- Benachrichtigungen funktionieren auf deinem System nicht

**Beispiel:**
```ini
ENABLE_NOTIFICATIONS=false
```
Dies deaktiviert Benachrichtigungen. Du siehst immer noch Ausgaben im Terminal, aber keine Pop-up-Nachrichten.

#### 6. DRY_RUN

```ini
DRY_RUN=false
```

**Was es macht:** Wenn auf `true` gesetzt, läuft das Script standardmäßig im Vorschaumodus (ohne Änderungen vorzunehmen).

**Werte:**
- `true` = Immer im Dry-Run-Modus laufen (nur Vorschau)
- `false` = Normaler Betrieb, tatsächliche Änderungen vornehmen (Standard)

**Wann aktivieren:**
- Du möchtest immer eine Vorschau vor dem Aktualisieren
- Du testest das Script
- Du möchtest eine zusätzliche Sicherheitsebene

**Hinweis:** Du kannst dies immer noch mit Kommandozeilen-Optionen überschreiben. Zum Beispiel:
- Wenn `DRY_RUN=true` in der Config, aber du führst `./update-all.sh` aus, wird es trotzdem Dry-Run sein
- Wenn `DRY_RUN=false` in der Config, aber du führst `./update-all.sh --dry-run` aus, wird es Dry-Run sein

**Beispiel:**
```ini
DRY_RUN=true
```
Dies macht, dass das Script immer im Vorschaumodus läuft. Es werden keine Änderungen vorgenommen, es sei denn, du überschreibst es explizit.

#### 7. MAX_LOG_FILES

```ini
MAX_LOG_FILES=10
```

**Was es macht:** Steuert, wie viele Log-Dateien behalten werden. Ältere Log-Dateien werden automatisch gelöscht.

**Werte:**
- Beliebige Zahl (Standard: 10)
- Das Script behält die N neuesten Log-Dateien
- Ältere Dateien werden automatisch gelöscht

**Was sind Log-Dateien?** Jedes Mal, wenn du das Script ausführst, erstellt es eine Log-Datei, die alles aufzeichnet, was passiert ist. Diese Dateien werden im `logs/`-Ordner gespeichert.

**Warum begrenzen?** Log-Dateien können Speicherplatz belegen. Durch die Begrenzung verhinderst du, dass deine Festplatte voll läuft.

**Beispiel:**
```ini
MAX_LOG_FILES=5
```
Dies behält nur die 5 neuesten Log-Dateien. Ältere werden automatisch gelöscht.

```ini
MAX_LOG_FILES=20
```
Dies behält die 20 neuesten Log-Dateien.

```ini
MAX_LOG_FILES=1
```
Dies behält nur die neueste Log-Datei (nicht empfohlen - du verlierst die Historie).

#### 8. ENABLE_COLORS

```ini
ENABLE_COLORS=true
```

**Was es macht:** Steuert, ob farbige Ausgabe im Terminal verwendet wird.

**Werte:**
- `true` = Farbige Ausgabe aktiviert (Standard)
- `false` = Keine Farben (nützlich für Logs/Redirects)

**Was sind Farben?** Das Script verwendet Farben, um die Ausgabe lesbarer zu machen:
- Cyan für Info-Nachrichten
- Grün für Erfolgs-Nachrichten
- Rot für Fehler-Nachrichten
- Gelb für Warnungen

**Wann deaktivieren:**
- Du leitest die Ausgabe in eine Datei um
- Dein Terminal unterstützt keine Farben
- Du bevorzugst reine Textausgabe

**Beispiel:**
```ini
ENABLE_COLORS=false
```
Dies deaktiviert farbige Ausgabe. Alle Nachrichten werden als reiner Text angezeigt.

#### 9. DOWNLOAD_RETRIES

```ini
DOWNLOAD_RETRIES=3
```

**Was es macht:** Steuert, wie oft das Script einen fehlgeschlagenen Download wiederholt.

**Werte:**
- Beliebige Zahl (Standard: 3)
- Das Script wiederholt bis zu N Mal, wenn ein Download fehlschlägt
- Wartet 2 Sekunden zwischen Wiederholungen

**Warum wiederholen?** Netzwerkprobleme können zu temporären Download-Fehlern führen. Wiederholen gibt dem Download eine weitere Chance, erfolgreich zu sein.

**Beispiel:**
```ini
DOWNLOAD_RETRIES=5
```
Dies wiederholt bis zu 5 Mal, wenn ein Download fehlschlägt.

```ini
DOWNLOAD_RETRIES=1
```
Dies versucht nur einmal (keine Wiederholungen).

#### 10. ENABLE_AUTO_UPDATE

```ini
ENABLE_AUTO_UPDATE=false
```

**Was es macht:** Aktiviert automatisches Update des Scripts selbst (mit Bestätigung).

**Werte:**
- `true` = Automatisches Update aktiviert (fragt nach Bestätigung)
- `false` = Zeigt nur Update-Benachrichtigung (Standard)

**Was passiert, wenn aktiviert?** Wenn eine neue Script-Version verfügbar ist, wird das Script:
1. Anzeigen, dass eine neue Version verfügbar ist
2. Fragen, ob du jetzt aktualisieren möchtest
3. Wenn ja, automatisch `git pull` ausführen, um zu aktualisieren
4. Wenn nein, nur Update-Anweisungen anzeigen

**Wann aktivieren:**
- Du möchtest bequeme Script-Updates
- Du vertraust dem Repository
- Du möchtest einfach auf dem neuesten Stand bleiben

**Beispiel:**
```ini
ENABLE_AUTO_UPDATE=true
```
Dies aktiviert automatische Script-Updates mit Bestätigung.

### Vollständiges Konfigurationsbeispiel

Hier ist ein vollständiges Beispiel einer Konfigurationsdatei mit Kommentaren:

```ini
# CachyOS Multi-Updater Konfigurationsdatei
# Kopiere diese Datei nach config.conf und passe sie an

# Update-Komponenten aktivieren/deaktivieren
ENABLE_SYSTEM_UPDATE=true      # CachyOS System-Pakete aktualisieren
ENABLE_AUR_UPDATE=true         # AUR-Pakete aktualisieren
ENABLE_CURSOR_UPDATE=false     # Cursor Editor nicht aktualisieren (wird über CachyOS aktualisiert)
ENABLE_ADGUARD_UPDATE=true     # AdGuard Home aktualisieren

# Logging-Einstellungen
MAX_LOG_FILES=10               # 10 neueste Log-Dateien behalten

# Benachrichtigungen
ENABLE_NOTIFICATIONS=true      # Desktop-Benachrichtigungen anzeigen

# Sicherheitseinstellungen
DRY_RUN=false                  # Tatsächliche Änderungen vornehmen (nicht Vorschaumodus)

# Erscheinungsbild
ENABLE_COLORS=true              # Farbige Terminal-Ausgabe

# Download-Einstellungen
DOWNLOAD_RETRIES=3             # Fehlgeschlagene Downloads bis zu 3 Mal wiederholen

# Script-Update
ENABLE_AUTO_UPDATE=false       # Automatisches Script-Update aktivieren (mit Bestätigung)
```

### Wie Konfiguration funktioniert

1. Das Script sucht nach `config.conf` im selben Ordner wie das Script
2. Wenn gefunden, liest es die Einstellungen
3. Einstellungen überschreiben die Standardwerte
4. Kommandozeilen-Optionen überschreiben Konfigurationsdatei-Einstellungen

**Prioritätsreihenfolge (höchste zu niedrigste):**
1. Kommandozeilen-Optionen (z.B. `--only-system`)
2. Konfigurationsdatei-Einstellungen
3. Standardwerte

**Beispiel:**
- Config-Datei sagt: `ENABLE_SYSTEM_UPDATE=false`
- Du führst aus: `./update-all.sh --only-system`
- Ergebnis: System-Updates laufen trotzdem (Kommandozeile überschreibt Config)

---

## 📝 Logs verstehen

### Was sind Logs?

Logs sind Textdateien, die alles aufzeichnen, was das Script macht. Sie sind wie ein Tagebuch dessen, was während jedes Updates passiert ist.

### Wo werden Logs gespeichert?

Logs werden im `logs/`-Ordner gespeichert, innerhalb des Script-Verzeichnisses.

**Vollständiger Pfad-Beispiel:**
```
/home/deinbenutzername/cachyos-multi-updater/logs/
```

### Log-Datei-Namensgebung

Jede Log-Datei hat einen Namen wie:
```
update-20241215-143022.log
```

**Aufschlüsselung:**
- `update-` = Präfix
- `20241215` = Datum (15. Dezember 2024)
- `143022` = Zeit (14:30:22 = 14:30:22 Uhr)
- `.log` = Dateiendung

### Was ist in einer Log-Datei?

Eine Log-Datei enthält:
- Zeitstempel jeder Aktion
- Was aktualisiert wurde
- Erfolgs-/Fehlermeldungen
- Fehlermeldungen (falls vorhanden)
- Versionsinformationen
- Systeminformationen

**Beispiel-Log-Eintrag:**
```
[2024-12-15 14:30:22] [INFO] CachyOS Multi-Updater Version 2.1.0
[2024-12-15 14:30:22] [INFO] Update gestartet...
[2024-12-15 14:30:23] [INFO] Starte CachyOS-Update...
[2024-12-15 14:30:45] [SUCCESS] CachyOS-Update erfolgreich
```

### Logs anzeigen

#### Alle Log-Dateien auflisten

```bash
ls -lh logs/
```

Dies zeigt alle Log-Dateien mit ihren Größen und Daten.

#### Eine spezifische Log-Datei anzeigen

```bash
cat logs/update-20241215-143022.log
```

Dies zeigt die gesamte Log-Datei.

#### Neueste Log anzeigen

```bash
cat logs/$(ls -t logs/ | head -1)
```

Oder einfach:
```bash
cat logs/update-*.log | tail -50
```

#### Log in Echtzeit beobachten

Wenn das Script läuft, kannst du zusehen, wie das Log geschrieben wird:

```bash
tail -f logs/update-*.log
```

Drücke `Strg+C`, um das Beobachten zu stoppen.

#### Logs nach Fehlern durchsuchen

```bash
grep -i error logs/update-*.log
```

Dies findet alle Zeilen, die "error" enthalten (Groß-/Kleinschreibung wird ignoriert).

#### Logs nach spezifischem Text durchsuchen

```bash
grep "Cursor" logs/update-*.log
```

Dies findet alle Zeilen, die "Cursor" erwähnen.

### Automatische Log-Bereinigung

Das Script löscht automatisch alte Log-Dateien, um Speicherplatz zu sparen. Standardmäßig behält es die 10 neuesten Logs.

**Wie es funktioniert:**
1. Nach jedem Lauf prüft das Script, wie viele Log-Dateien existieren
2. Wenn es mehr als `MAX_LOG_FILES` gibt, löscht es die ältesten
3. Nur die N neuesten Dateien werden behalten

**Bereinigung konfigurieren:**
Setze `MAX_LOG_FILES` in `config.conf` (siehe Konfigurationsabschnitt).

---

## 🐛 Fehlerbehebung

### Allgemeine Fehlerbehebungsschritte

1. **Prüfe zuerst die Logs!** Die meisten Probleme werden geloggt. Siehe den Abschnitt "Logs verstehen" oben.

2. **Versuche den Dry-Run-Modus**, um zu sehen, was passieren würde, ohne Änderungen vorzunehmen:
   ```bash
   ./update-all.sh --dry-run
   ```

3. **Prüfe deine Internetverbindung** - Updates erfordern Internet.

4. **Stelle sicher, dass du sudo-Zugriff hast:**
   ```bash
   sudo -v
   ```
   Wenn dies fehlschlägt, hast du keinen sudo-Zugriff.

### Spezifische Probleme und Lösungen

#### Problem: Script sagt "Update läuft bereits!"

**Was das bedeutet:** Das Script hat eine Lock-Datei gefunden, was bedeutet, dass es denkt, dass bereits ein Update läuft.

**Lösungen:**

1. **Prüfe, ob ein Update tatsächlich läuft:**
   ```bash
   ps aux | grep update-all.sh
   ```
   Wenn du einen Prozess siehst, warte, bis er fertig ist.

2. **Wenn kein Prozess läuft, lösche die Lock-Datei:**
   ```bash
   rm ~/cachyos-multi-updater/.update-all.lock
   ```
   (Passe den Pfad an, wenn dein Script woanders ist)

3. **Warum ist das passiert?** Das Script könnte abgestürzt oder unterbrochen worden sein und die Lock-Datei zurückgelassen haben.

#### Problem: "Permission denied" beim Ausführen des Scripts

**Was das bedeutet:** Die Script-Datei hat keine Ausführungsrechte.

**Lösungen:**

1. **Mache es ausführbar:**
   ```bash
   chmod +x update-all.sh
   ```

2. **Überprüfe, ob es funktioniert hat:**
   ```bash
   ls -l update-all.sh
   ```
   Du solltest `x` in den Berechtigungen sehen (wie `-rwxr-xr-x`).

#### Problem: "Command not found" für yay/paru

**Was das bedeutet:** Du hast keinen AUR-Helper installiert, oder er ist nicht in deinem PATH.

**Lösungen:**

1. **Prüfe, ob installiert:**
   ```bash
   which yay
   which paru
   ```

2. **Wenn nicht installiert, installiere einen:**

   **yay installieren:**
   ```bash
   git clone https://aur.archlinux.org/yay.git
   cd yay
   makepkg -si
   ```

   **paru installieren:**
   ```bash
   git clone https://aur.archlinux.org/paru.git
   cd paru
   makepkg -si
   ```

3. **Oder deaktiviere AUR-Updates** in `config.conf`:
   ```ini
   ENABLE_AUR_UPDATE=false
   ```

#### Problem: Cursor wird nicht aktualisiert

**Mögliche Ursachen und Lösungen:**

1. **Cursor nicht installiert:**
   ```bash
   which cursor
   ```
   Wenn dies nichts zeigt, ist Cursor nicht installiert oder nicht im PATH.

2. **Internetverbindung prüfen:**
   ```bash
   ping api2.cursor.sh
   ```

3. **Log-Dateien prüfen** auf spezifische Fehlermeldungen:
   ```bash
   grep -i cursor logs/update-*.log
   ```

4. **Berechtigungsprobleme:**
   - Stelle sicher, dass du in Cursors Installationsverzeichnis schreiben kannst
   - Prüfe Log-Dateien auf Berechtigungsfehler

5. **Cursor-Updates deaktivieren**, wenn du es nicht verwendest:
   ```ini
   ENABLE_CURSOR_UPDATE=false
   ```

**Hinweis:** Falls Cursor über CachyOS-Repositories aktualisiert wird, ist diese Funktion nicht nötig und kann deaktiviert werden.

#### Problem: AdGuard Home wird nicht aktualisiert

**Mögliche Ursachen und Lösungen:**

1. **AdGuard Home nicht am erwarteten Ort:**
   ```bash
   ls -l ~/AdGuardHome/AdGuardHome
   ```
   Wenn dies fehlschlägt, ist AdGuard Home nicht am erwarteten Ort.

2. **Prüfe, ob der Service existiert:**
   ```bash
   systemctl --user status AdGuardHome
   ```

3. **Log-Dateien prüfen** auf spezifische Fehler:
   ```bash
   grep -i adguard logs/update-*.log
   ```

4. **AdGuard-Updates deaktivieren**, wenn du es nicht verwendest:
   ```ini
   ENABLE_ADGUARD_UPDATE=false
   ```

#### Problem: Sudo-Passwort-Aufforderung erscheint ständig

**Was das bedeutet:** Das Script braucht sudo-Zugriff für System- und AUR-Updates.

**Lösungen:**

1. **Gib dein Passwort ein, wenn danach gefragt wird** - Das ist normal und erforderlich.

2. **Konfiguriere sudo, um kein Passwort zu erfordern** (fortgeschritten, aus Sicherheitsgründen nicht empfohlen):
   ```bash
   sudo visudo
   ```
   Füge Zeile hinzu:
   ```
   deinbenutzername ALL=(ALL) NOPASSWD: /usr/bin/pacman
   ```
   (Ersetze `deinbenutzername` mit deinem tatsächlichen Benutzernamen)

3. **Oder deaktiviere Updates, die sudo erfordern:**
   ```ini
   ENABLE_SYSTEM_UPDATE=false
   ENABLE_AUR_UPDATE=false
   ```

#### Problem: Script läuft, aber es scheint nichts zu passieren

**Mögliche Ursachen:**

1. **Alles ist bereits auf dem neuesten Stand** - Das ist normal! Das Script aktualisiert nur, wenn Updates verfügbar sind.

2. **Dry-Run-Modus ist aktiviert** - Prüfe deine `config.conf`:
   ```ini
   DRY_RUN=true
   ```
   Ändere auf `false`, um tatsächliche Änderungen vorzunehmen.

3. **Alle Updates sind deaktiviert** - Prüfe deine `config.conf` - alle `ENABLE_*`-Optionen könnten `false` sein.

4. **Prüfe die Logs** - Sie werden dir sagen, was passiert ist:
   ```bash
   cat logs/$(ls -t logs/ | head -1)
   ```

#### Problem: "No space left on device"

**Was das bedeutet:** Deine Festplatte ist voll.

**Lösungen:**

1. **Speicherplatz freigeben:**
   ```bash
   df -h
   ```
   Dies zeigt die Festplattennutzung.

2. **Paket-Cache bereinigen:**
   ```bash
   sudo pacman -Sc
   ```

3. **Alte Log-Dateien löschen:**
   ```bash
   rm logs/update-*.log
   ```
   (Behalte neuere, wenn du sie brauchst)

4. **MAX_LOG_FILES reduzieren** in `config.conf`:
   ```ini
   MAX_LOG_FILES=5
   ```

### Hilfe bekommen

Wenn du ein Problem nicht lösen kannst:

1. **Prüfe die Logs** - Sie enthalten detaillierte Fehlermeldungen
2. **Versuche den Dry-Run-Modus** - Sieh, was passieren würde
3. **Prüfe diesen Fehlerbehebungsabschnitt** - Dein Problem könnte aufgelistet sein
4. **Erstelle ein Issue auf GitHub:**
   - Gehe zu https://github.com/SunnyCueq/cachyos-multi-updater/issues
   - Klicke auf "New Issue"
   - Beschreibe dein Problem
   - Füge relevante Log-Auszüge hinzu
   - Beschreibe, was du versucht hast

---

## ❓ FAQ (Häufig gestellte Fragen)

### F: Wie oft sollte ich dieses Script ausführen?

**A:** Das hängt von deiner Präferenz ab. Viele Benutzer führen es aus:
- Täglich (für Sicherheits-Updates)
- Wöchentlich (ausgewogener Ansatz)
- Vor wichtigen Arbeitssitzungen
- Wenn über Updates benachrichtigt

Es gibt keine "richtige" Häufigkeit - wähle, was für dich funktioniert!

### F: Ist es sicher, es automatisch (via cron) auszuführen?

**A:** Ja, aber mit Vorsicht:
- Das Script hat Fehlerbehandlung und wird dein System nicht kaputt machen, wenn ein Update fehlschlägt
- Es erfordert jedoch sudo-Zugriff, also konfiguriere sudo richtig
- Empfohlen: Teste es zuerst manuell, dann richte Automatisierung ein
- Erwäge, `--dry-run` in cron zu verwenden, um Änderungen vorherzusehen

### F: Was passiert, wenn das Script abstürzt oder unterbrochen wird?

**A:** Das Script ist darauf ausgelegt, Unterbrechungen zu handhaben:
- Lock-Datei verhindert mehrere gleichzeitige Läufe
- Wenn unterbrochen, musst du möglicherweise `.update-all.lock` manuell löschen
- Logs zeigen, was vor der Unterbrechung abgeschlossen wurde
- System-Updates, die gestartet wurden, werden abgeschlossen (pacman kümmert sich darum)
- AUR-Updates, die gestartet wurden, könnten manuelle Aufmerksamkeit benötigen

### F: Kann ich das auf normalem Arch Linux verwenden?

**A:** Ja! Während es für CachyOS entwickelt wurde, funktioniert es auch auf Arch Linux. Stelle nur sicher:
- Du hast pacman installiert (Standard auf Arch)
- AUR-Helper funktionieren genauso
- Cursor- und AdGuard Home-Updates funktionieren identisch

### F: Schließt und startet das Script Cursor automatisch?

**A:** Nein, das Script schließt oder startet Cursor NICHT automatisch. Es:
- Prüft nur, ob Cursor läuft (zeigt eine Warnung, falls ja)
- Lädt und installiert das Update
- Du kannst Cursor manuell schließen/starten, falls nötig

**Warum?** Automatisches Schließen/Starten kann störend sein. Du hast volle Kontrolle darüber, wann Cursor läuft.

**Hinweis:** Falls Cursor über CachyOS-Repositories aktualisiert wird, ist diese Funktion nicht nötig und kann deaktiviert werden.

### F: Wird dieses Script mein System kaputt machen?

**A:** Das Script ist darauf ausgelegt, sicher zu sein:
- Es verwendet Standard-Paketmanager (pacman, yay/paru)
- Es hat Fehlerbehandlung, um Kaskadenfehler zu verhindern
- Es erstellt Backups der AdGuard Home-Konfiguration
- Es loggt alles für Fehlerbehebung

Jedoch trägt jedes System-Update ein gewisses Risiko. Verwende `--dry-run` zuerst, wenn du unsicher bist!

### F: Kann ich anpassen, was aktualisiert wird?

**A:** Ja! Mehrere Möglichkeiten:
1. **Konfigurationsdatei** (`config.conf`) - Komponenten aktivieren/deaktivieren
2. **Kommandozeilen-Flags** - `--only-system`, `--only-aur`, etc.
3. **Beides kombinieren** - Verwende Config für Standardeinstellungen, Flags für einmalige Änderungen

### F: Was, wenn ich yay oder paru nicht installiert habe?

**A:** Kein Problem! Das Script wird:
- AUR-Updates überspringen, wenn kein Helper gefunden wird
- Eine Warnmeldung loggen
- Mit anderen Updates fortfahren
- Du kannst AUR-Updates in `config.conf` deaktivieren, um die Warnung zu unterdrücken

### F: Wie aktualisiere ich das Script selbst?

**A:** Wenn du mit Git geklont hast:
```bash
cd ~/cachyos-multi-updater
git pull
```

Wenn du als ZIP heruntergeladen hast, lade die neueste Version von GitHub herunter.

**Hinweis:** Das Script prüft jetzt automatisch auf neue Versionen am Ende jedes Updates!

### F: Das Script fragt mehrmals nach meinem Passwort. Warum?

**A:** Das hängt von deiner sudo-Konfiguration ab:
- Standardmäßig fragt sudo jedes Mal nach dem Passwort
- Das Script braucht sudo für System- und AUR-Updates
- Du kannst sudo so konfigurieren, dass es sich dein Passwort merkt (siehe Fehlerbehebung)
- Oder deaktiviere System/AUR-Updates, wenn du sie nicht brauchst

### F: Kann ich sehen, was aktualisiert wird, bevor ich es ausführe?

**A:** Ja! Verwende den Dry-Run-Modus:
```bash
./update-all.sh --dry-run
```

Dies zeigt, was aktualisiert WÜRDE, ohne Änderungen vorzunehmen.

### F: Was ist update-all.1? Was kann sie? Wozu braucht man sie?

**A:** `update-all.1` ist eine **Man-Page** (Manual Page) - ein Standard-Dokumentationsformat für Unix/Linux.

**Was ist eine Man-Page?**
- Es ist die traditionelle Art, Kommandozeilen-Tools auf Linux/Unix-Systemen zu dokumentieren
- Sie bietet prägnante, technische Dokumentation, die Unix-Konventionen folgt
- Es ist das, was du siehst, wenn du `man ls` oder `man pacman` auf Linux eingibst

**Was kann sie?**
- Dokumentation direkt im Terminal anzeigen: `man ./update-all.1`
- Wenn systemweit installiert: `man update-all` (funktioniert von überall)
- Schnelle Referenz für Befehlsoptionen und Verwendung
- Folgt Standard-Unix-Dokumentationsformat

**Wozu braucht man sie?**
- **Du brauchst sie wahrscheinlich nicht** - die README-Dateien sind detaillierter und anfängerfreundlicher
- Sie ist nützlich, wenn du mit Unix-Dokumentationsstandards vertraut bist
- Einige Linux-Benutzer bevorzugen Man-Pages für schnelle Referenz
- Sie ist optional - du kannst sie ignorieren, wenn du die README bevorzugst

**Wie verwendet man sie:**
```bash
# Man-Page direkt anzeigen
man ./update-all.1

# Oder wenn systemweit installiert (nach Installation)
man update-all
```

**Installation (optional):**
Wenn du sie systemweit verfügbar machen möchtest:
```bash
sudo cp update-all.1 /usr/local/share/man/man1/
sudo mandb
```
Dann kannst du `man update-all` von überall verwenden.

### F: Was, wenn ich ein Problem habe, das nicht in der FAQ abgedeckt ist?

**A:** Prüfe diese Ressourcen in dieser Reihenfolge:
1. **Logs** - Prüfe den `logs/`-Ordner für detaillierte Informationen
2. **Fehlerbehebungsabschnitt** - Sieh den Fehlerbehebungsleitfaden oben
3. **GitHub Issues** - Suche nach bestehenden Issues
4. **Erstelle ein Issue** - Beschreibe dein Problem mit Log-Auszügen

---

## 📅 Versionshistorie

Für die vollständige Versionshistorie und Changelog siehe [GitHub Releases](https://github.com/SunnyCueq/cachyos-multi-updater/releases).

---

## 📄 Lizenz

Dieses Projekt ist Open Source. Du kannst es frei verwenden, modifizieren und verteilen.

## 🤝 Beitragen

Verbesserungen und Fehlerberichte sind willkommen! Bitte erstelle ein Issue oder Pull Request auf [GitHub](https://github.com/SunnyCueq/cachyos-multi-updater).

## 📧 Support

Bei Fragen oder Problemen:
1. Prüfe zuerst die Log-Dateien in `logs/`
2. Prüfe den [Fehlerbehebungsabschnitt](#-fehlerbehebung) oben
3. Erstelle ein Issue auf [GitHub](https://github.com/SunnyCueq/cachyos-multi-updater)
4. Beschreibe das Problem so detailliert wie möglich (inklusive Log-Auszüge)

## 🔗 Links

- **GitHub Repository:** https://github.com/SunnyCueq/cachyos-multi-updater
- **Issues:** https://github.com/SunnyCueq/cachyos-multi-updater/issues

---

**Viel Erfolg mit deinen Updates! 🎉**
