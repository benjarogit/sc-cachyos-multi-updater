# 🚀 GUI Startanleitung

## ✅ Status-Check

**Python:** ✅ 3.13.7  
**PyQt6:** ✅ 6.10.1 installiert  
**update-all.sh:** ✅ Gefunden  

## 🎯 Schnellstart

### Einfachste Methode (empfohlen):

```bash
cd /home/benny/Dokumente/cachyos-multi-updater
./gui/start.sh
```

### Alternative Methoden:

**Option 1: Direkt mit Python**
```bash
cd /home/benny/Dokumente/cachyos-multi-updater
python3 gui/main.py
```

**Option 2: Als ausführbare Datei**
```bash
cd /home/benny/Dokumente/cachyos-multi-updater
chmod +x gui/main.py
./gui/main.py
```

**Option 3: Mit Python-Modul**
```bash
cd /home/benny/Dokumente/cachyos-multi-updater
python3 -m gui.main
```

## 📋 Voraussetzungen

- ✅ Python 3.8+ (du hast 3.13.7)
- ✅ PyQt6 installiert (du hast 6.10.1)
- ✅ update-all.sh vorhanden (✅ gefunden)

## 🎮 Verwendung

1. **Updates prüfen**: Klicke auf "Check for Updates" (Dry-Run Modus)
2. **Updates starten**: Klicke auf "Start Updates"
3. **Einstellungen**: Klicke auf "Settings" um Optionen zu konfigurieren
4. **Logs ansehen**: Klicke auf "View Logs" um Log-Dateien zu durchsuchen

## 🖥️ Desktop-Verknüpfung erstellen (optional)

Für einfachen Start aus dem Anwendungsmenü:

```bash
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/cachyos-multi-updater-gui.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=CachyOS Multi-Updater GUI
Comment=Graphical interface for system updates
Exec=python3 /home/benny/Dokumente/cachyos-multi-updater/gui/main.py
Icon=system-software-update
Terminal=false
Categories=System;Settings;
EOF

chmod +x ~/.local/share/applications/cachyos-multi-updater-gui.desktop
```

## 🔧 Troubleshooting

### PyQt6 nicht installiert

**Fehler:** `ModuleNotFoundError: No module named 'PyQt6'`

**Lösung:**
```bash
pip3 install PyQt6
# oder
pip3 install -r requirements-gui.txt
```

### Script nicht gefunden

**Fehler:** `update-all.sh not found`

**Lösung:**
```bash
export SCRIPT_DIR=/home/benny/Dokumente/cachyos-multi-updater
python3 gui/main.py
```

## 📚 Weitere Informationen

- Detaillierte GUI-Dokumentation: `gui/README.md`
- Hauptprojekt-Dokumentation: `README.md`
