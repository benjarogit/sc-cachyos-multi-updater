# Testing Guide

## Manual Testing Checklist

### Phase 5.1: Functionality Testing

#### Basic Functionality
- [ ] GUI starts without errors
- [ ] Main window displays correctly
- [ ] All components (System, AUR, Cursor, AdGuard, Flatpak) are visible
- [ ] Checkboxes work correctly
- [ ] Buttons are enabled/disabled appropriately

#### Update Operations
- [ ] "Check for Updates" button works (dry-run mode)
- [ ] "Start Updates" button works
- [ ] Progress bar updates correctly
- [ ] Output text area shows real-time updates
- [ ] Stop button works (if applicable)

#### Settings Dialog
- [ ] Settings dialog opens
- [ ] All tabs are accessible
- [ ] Configuration can be saved
- [ ] Configuration persists after restart

#### i18n Testing
- [ ] Language detection works (auto)
- [ ] Language can be changed to German
- [ ] Language can be changed to English
- [ ] All UI elements are translated
- [ ] Language persists after restart

#### Theme Testing
- [ ] Theme detection works (auto)
- [ ] Theme can be changed to dark
- [ ] Theme can be changed to light
- [ ] Theme persists after restart

#### Error Handling
- [ ] Missing update-all.sh shows error message
- [ ] Network errors are handled gracefully
- [ ] Invalid configuration shows warnings
- [ ] Logs are created for errors

#### Log Viewer
- [ ] Log viewer opens
- [ ] Log files are listed
- [ ] Log content is displayed correctly
- [ ] Log filtering works

#### Version Check
- [ ] Version check runs on startup
- [ ] Update notification appears if update available
- [ ] Manual version check works

## Automated Testing

Run pytest tests:
```bash
cd cachyos-multi-updater
pip install -r requirements-gui.txt
pytest gui/tests/ -v
```

## Test Coverage

Current test coverage:
- ConfigManager: 11 tests
- i18n: 9 tests
- Widgets: 5 tests
- VersionChecker: 10 tests
- BashWrapper: 9 tests

Total: 44 tests

