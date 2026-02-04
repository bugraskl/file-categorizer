# Changelog

All notable changes to File Categorizer will be documented in this file.

## [1.0.0] - 2024-02-04

### Added
- 🎉 Initial release
- 10 categorization modes:
  - By extension (jpg, pdf, docx...)
  - By MIME type (Images, Videos, Documents)
  - By creation date
  - By modification date
  - By size (0-1MB, 1-10MB, 10-100MB...)
  - By name pattern (invoice, IMG_, screenshot...)
  - Similarity analysis (Levenshtein, Jaro-Winkler)
  - Dynamic size histogram
  - Same-name file grouping
  - Multi-criteria (AND/OR combinations)
- Simulation mode (preview before moving)
- Undo feature with JSON operation logs
- Language selection for folder names (English/Turkish)
- Progress indicator with cancel option
- Cross-platform support (Windows, macOS, Linux)

### Features
- No AI - fully algorithmic and deterministic
- Minimal, flat desktop UI design
- Dark/light theme support ready
- Python backend for file operations
- Electron frontend for cross-platform compatibility

## Download

| Platform | File |
|----------|------|
| Windows | `File-Categorizer-1.0.0-x64.exe` |
| macOS (Intel) | `File-Categorizer-1.0.0-x64.dmg` |
| macOS (Apple Silicon) | `File-Categorizer-1.0.0-arm64.dmg` |
| Linux | `File-Categorizer-1.0.0-x64.AppImage` |

## Installation

### Windows
1. Download the `.exe` file
2. Run the installer
3. Follow the installation wizard

### macOS
1. Download the `.dmg` file
2. Open the disk image
3. Drag the app to Applications folder
4. First run: Right-click → Open (to bypass Gatekeeper)

### Linux
1. Download the `.AppImage` file
2. Make executable: `chmod +x File-Categorizer-*.AppImage`
3. Run: `./File-Categorizer-*.AppImage`
