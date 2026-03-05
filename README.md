# macOS Windows Keyboard Setup

Make macOS behave like Windows when using an external Windows keyboard (tested with Logitech).

This project contains all the configuration files and a comprehensive setup guide for remapping keys, window management, app switching, and terminal shortcuts.

## What's Included

| File | Purpose | System Location |
|------|---------|-----------------|
| `config/karabiner/karabiner.json` | Key remapping (18 rules + per-device mods) | `~/.config/karabiner/karabiner.json` |
| `config/rectangle/RectangleConfig.json` | Window snapping (Win+Arrows) | Import via Rectangle UI |
| `config/keybindings/DefaultKeyBinding.dict` | Page Up/Down cursor movement | `~/Library/KeyBindings/DefaultKeyBinding.dict` |
| `config/ghostty/config` | Ghostty terminal config (tmux autostart) | `~/.config/ghostty/config` |
| `config/ghostty/icon_256x256@2x.png` | Custom Ghostty icon | `~/.config/ghostty/icon_256x256@2x.png` |
| `macOS-Windows-Setup-Guide.md` | Full setup guide with explanations | — |

## Quick Install

```bash
./install.sh
```

This copies config files to their correct system locations (backs up existing files first). You'll still need to:

1. Install apps: `brew install --cask karabiner-elements rectangle alt-tab ghostty unnaturalscrollwheels`
2. Grant Accessibility permissions: Karabiner, Rectangle, AltTab
3. Grant Input Monitoring: Karabiner
4. Add to Login Items: Karabiner, Rectangle, AltTab, UnnaturalScrollWheels
5. Import Rectangle config: Rectangle → Settings → Import

## Key Shortcuts (Cheat Sheet)

| Shortcut | Action |
|----------|--------|
| Ctrl+C/V/X/Z/A/S | Copy/Paste/Cut/Undo/SelectAll/Save |
| Ctrl+Arrow | Move by word |
| Win+Left/Right/Up/Down | Snap/Maximize/Restore window |
| Win+D | Show Desktop (hide all apps) |
| Alt+Tab | Switch windows |
| Alt+Space | Spotlight search |
| Win+L | Lock screen |
| F11 | Toggle fullscreen |
| Win+1/2/3 | Chrome / Ghostty / IPython |

See [macOS-Windows-Setup-Guide.md](macOS-Windows-Setup-Guide.md) for the full guide.
