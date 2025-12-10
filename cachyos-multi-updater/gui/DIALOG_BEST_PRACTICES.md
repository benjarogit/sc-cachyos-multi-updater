# PyQt6 Dialog Best Practices - Implementierungsleitfaden

## Übersicht
Dieses Dokument beschreibt die PyQt6 Dialog Best Practices, die wir in diesem Projekt befolgen.

## Best Practices die wir befolgen

### 1. Modal Dialoge mit `exec()`
✅ **Wir befolgen das:**
- Modale Dialoge mit `setModal(True)` und `exec()` verwenden
- `exec()` blockiert den Event-Loop bis Dialog geschlossen wird
- Rückgabewert: `QDialog.DialogCode.Accepted` oder `QDialog.DialogCode.Rejected`

**Beispiel aus unserem Code:**
```python
dialog = UpdateConfirmationDialog(self)
if dialog.exec() == QDialog.DialogCode.Accepted:
    # User hat "Ja" geklickt
    self.start_updates()
```

### 2. Parent setzen
✅ **Wir befolgen das:**
- Immer `parent=self` beim Erstellen von Dialogen setzen
- Ermöglicht korrekte Fenster-Hierarchie und automatisches Cleanup

**Beispiel:**
```python
dialog = UpdateConfirmationDialog(self)  # parent=self
```

### 3. Accept/Reject Pattern
✅ **Wir befolgen das:**
- `accept()` und `reject()` verwenden, nicht `close()`
- `accept()` setzt Dialog-Result auf `Accepted`
- `reject()` setzt Dialog-Result auf `Rejected`

**Beispiel:**
```python
def accept(self):
    """User clicked Yes"""
    super().accept()  # Setzt Result auf Accepted

def reject(self):
    """User clicked No"""
    super().reject()  # Setzt Result auf Rejected
```

### 4. Layout Manager verwenden
✅ **Wir befolgen das:**
- `QVBoxLayout` für vertikale Anordnung
- `QHBoxLayout` für horizontale Anordnung
- `setLayout()` am Ende aufrufen

**Beispiel:**
```python
layout = QVBoxLayout()
layout.addWidget(label)
layout.addLayout(button_layout)
self.setLayout(layout)
```

### 5. Window Flags setzen
✅ **Wir befolgen das:**
- Help-Button entfernen: `~Qt.WindowType.WindowContextHelpButtonHint`
- Modal setzen: `setModal(True)`

**Beispiel:**
```python
self.setModal(True)
self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
```

### 6. Standard-Button-Layouts
✅ **Wir befolgen das:**
- Konsistente Button-Anordnung (Cancel links, OK/Yes rechts)
- `setDefault(True)` für Standard-Button
- `addStretch()` für richtige Button-Positionierung

**Beispiel:**
```python
button_layout = QHBoxLayout()
cancel_btn = QPushButton("Cancel")
cancel_btn.clicked.connect(self.reject)
button_layout.addWidget(cancel_btn)

button_layout.addStretch()

ok_btn = QPushButton("OK")
ok_btn.clicked.connect(self.accept)
ok_btn.setDefault(True)
button_layout.addWidget(ok_btn)
```

### 7. Dialog-Instanzen nicht global halten
✅ **Wir befolgen das:**
- Dialog-Instanzen lokal erstellen
- Nach `exec()` wird Dialog automatisch gelöscht (wenn parent gesetzt)

**Beispiel:**
```python
# ✅ RICHTIG: Lokale Instanz
dialog = UpdateConfirmationDialog(self)
if dialog.exec() == QDialog.DialogCode.Accepted:
    # Dialog wird automatisch gelöscht
    pass

# ❌ FALSCH: Globale Instanz
self.dialog = UpdateConfirmationDialog(self)
```

## Best Practices die wir noch verbessern können

### 1. Dialog-Validierung vor accept()
⚠️ **Könnte verbessert werden:**
- Eingaben validieren bevor `accept()` aufgerufen wird
- Bei ungültigen Eingaben Dialog nicht schließen

**Beispiel:**
```python
def accept(self):
    """Validate before accepting"""
    if not self.validate_input():
        # Zeige Fehlermeldung, Dialog bleibt offen
        QMessageBox.warning(self, "Error", "Invalid input")
        return
    super().accept()
```

### 2. Dialog-Größe und Position
⚠️ **Könnte verbessert werden:**
- `setMinimumSize()` / `setMaximumSize()` für bessere Größenkontrolle
- `move()` für Positionierung (optional)

**Aktuell:**
```python
self.setMinimumWidth(450)  # Nur minimale Breite
```

**Könnte sein:**
```python
self.setMinimumSize(450, 200)
self.setMaximumSize(800, 600)
```

### 3. Keyboard Shortcuts
⚠️ **Könnte verbessert werden:**
- Escape-Taste für Cancel/Reject
- Enter-Taste für Accept (wird bereits durch `setDefault(True)` unterstützt)

**Beispiel:**
```python
from PyQt6.QtGui import QShortcut, QKeySequence

# Escape für Cancel
shortcut = QShortcut(QKeySequence("Escape"), self)
shortcut.activated.connect(self.reject)
```

### 4. Dialog-Result prüfen
✅ **Wir befolgen das bereits:**
- Immer `exec()` Rückgabewert prüfen
- Nur bei `Accepted` weitermachen

**Beispiel:**
```python
if dialog.exec() == QDialog.DialogCode.Accepted:
    # Nur wenn User "Ja" geklickt hat
    self.start_updates()
```

## Zusammenfassung

**Was wir gut machen:**
- ✅ Modal Dialoge mit `exec()`
- ✅ Parent setzen
- ✅ Accept/Reject Pattern
- ✅ Layout Manager
- ✅ Window Flags
- ✅ Standard-Button-Layouts
- ✅ Lokale Dialog-Instanzen

**Was wir verbessern könnten:**
- ⚠️ Eingabe-Validierung vor accept()
- ⚠️ Bessere Größenkontrolle
- ⚠️ Keyboard Shortcuts (Escape)

## Referenzen
- [PyQt6 QDialog Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qdialog.html)
- [Qt Dialog Best Practices](https://doc.qt.io/qt-6/qdialog.html)

