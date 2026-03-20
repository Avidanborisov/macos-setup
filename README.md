# macOS Windows Keyboard Setup

Make macOS behave like Windows when using an external Windows keyboard (tested with Logitech).

This repo contains all configuration files and an automated installer for remapping keys, window management, app switching, and terminal shortcuts. All config files live in the `config/` directory — the install script copies them to their system locations.

Based on [this blog post](https://imoskvin.com/blog/macos-like-windows/).

---

## Table of Contents

1. [Quick Install](#quick-install)
2. [What's Included](#whats-included)
3. [macOS System Settings](#3-macos-system-settings)
4. [Karabiner-Elements — Key Remapping](#4-karabiner-elements--key-remapping)
5. [Rectangle — Window Snapping](#5-rectangle--window-snapping)
6. [AltTab — Window Switching](#6-alttab--window-switching)
7. [Clipboard History — Maccy (Win+V)](#7-clipboard-history--maccy-win-v)
8. [Page Up / Page Down — Cursor Movement](#8-page-up--page-down--cursor-movement)
9. [Red X Button — Quit on Close](#9-red-x-button--quit-on-close)
10. [Scroll Direction](#10-scroll-direction)
11. [VS Code](#11-vs-code)
12. [Keyboard Cheat Sheet](#12-keyboard-cheat-sheet)
13. [Known Limitations](#13-known-limitations)

---

## Quick Install

```bash
./install.sh
```

This will:

1. **Install apps** via Homebrew: Karabiner-Elements, Rectangle, AltTab, Maccy, Ghostty, UnnaturalScrollWheels, RedQuits
2. **Apply macOS defaults**: auto-hide Dock, F-keys as standard, English locale, Ctrl+Space input switching
3. **Configure AltTab**: Control as hold key, hide minimized/hidden windows
4. **Copy config files** to their system locations (backs up existing files first):
   - `config/karabiner/karabiner.json` → `~/.config/karabiner/karabiner.json`
   - `config/keybindings/DefaultKeyBinding.dict` → `~/Library/KeyBindings/DefaultKeyBinding.dict`
   - `config/ghostty/config` → `~/.config/ghostty/config`
5. **Add apps to Login Items** so they auto-start on login

After running, you'll still need to:

1. Grant **Accessibility** permissions (System Settings → Privacy & Security → Accessibility):
   - Karabiner (`karabiner_grabber`), Rectangle, AltTab
   - Maccy (only if you enable "Paste automatically")
2. Grant **Input Monitoring** (System Settings → Privacy & Security → Input Monitoring):
   - Karabiner (`karabiner_grabber`, `karabiner_observer`)
3. **Import Rectangle config**: Rectangle → Settings → Import → select `config/rectangle/RectangleConfig.json`
4. **VS Code**: add `"editor.mouseWheelZoom": true` to settings.json
5. Add to `~/.zshrc`: `export LC_TIME=en_US.UTF-8`
6. **Restart macOS** to apply all keyboard shortcut changes

If macOS blocks background items, allow them in System Settings → General → Login Items.

---

## What's Included

| File | Purpose | System Location |
|------|---------|-----------------|
| `config/karabiner/karabiner.json` | Key remapping (19 rules + per-device mods) | `~/.config/karabiner/karabiner.json` |
| `config/alttab/holdShortcut.plist` | AltTab hold shortcut (Control, in ShortcutRecorder binary format) | Written to AltTab prefs via PlistBuddy |
| `config/rectangle/RectangleConfig.json` | Window snapping (Win+Arrows) | Import via Rectangle UI |
| `config/keybindings/DefaultKeyBinding.dict` | Page Up/Down cursor movement | `~/Library/KeyBindings/DefaultKeyBinding.dict` |
| `config/ghostty/config` | Ghostty terminal config (tmux autostart) | `~/.config/ghostty/config` |
| `config/ghostty/icon_256x256@2x.png` | Custom Ghostty icon | `~/.config/ghostty/icon_256x256@2x.png` |
| `bin/src/toggle-input-source.swift` | Swift source for input source toggling (compiled during install) | `~/.local/bin/toggle-input-source` |
| `install.sh` | Automated installer (apps, defaults, config files) | — |

---

## 3. macOS System Settings

These settings are applied automatically by `./install.sh`. This section documents what they do for reference.

```bash
# Auto-hide Dock
defaults write com.apple.dock autohide -bool true
killall Dock

# F-keys as standard function keys (built-in keyboard)
defaults write -g com.apple.keyboard.fnState -bool true

# Force English locale system-wide
defaults write NSGlobalDomain AppleLanguages -array en
defaults write NSGlobalDomain AppleLocale -string en_US
defaults write NSGlobalDomain AppleCollationOrder -string en
killall SystemUIServer
```

Add to `~/.zshrc` to ensure terminal dates/times are in English:

```bash
export LC_TIME=en_US.UTF-8
```

### Keyboard Shortcuts (via defaults)

```bash
# Enable Input Source switching on Ctrl+Space (used by Win+Space Karabiner rule)
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 60 \
    '<dict><key>enabled</key><true/><key>value</key><dict><key>parameters</key><array><integer>32</integer><integer>49</integer><integer>262144</integer></array><key>type</key><string>standard</string></dict></dict>'

# Apply changes
/System/Library/PrivateFrameworks/SystemAdministration.framework/Resources/activateSettings -u
```

---

## 4. Karabiner-Elements — Key Remapping

### 4.1 How it works

On a Windows keyboard the bottom-left modifiers are: `Ctrl | Win | Alt`. On macOS the same physical positions are: `Control | Option | Command`.

**Simple modifications** swap the modifier keys so each physical key does what its label says. Because the MacBook's built-in keyboard has a different physical layout (`Control | Option | Command`) from the external Windows keyboard (`Ctrl | Win | Alt`), the modifier mapping is **per-device**.

#### Profile-level simple modifications (apply to all keyboards, tuned for built-in)

| From | To | Effect on built-in keyboard |
|---|---|---|
| `left_control` | `left_command` | Ctrl → Cmd (copy/paste/undo) |
| `left_command` | `left_control` | Cmd → Control (acts as Alt — AltTab, etc.) |
| `right_control` | `right_command` | Same for right side |
| `right_command` | `right_control` | Same for right side |
| `non_us_backslash` | `grave_accent_and_tilde` | § key → `` ` `` / `~` |

On the built-in keyboard, **Option stays as Option** (no mapping), so it acts as the Win key.

#### Device-specific overrides (Logitech external keyboard — vendor 1133, product 50475)

| From | To | Effect on external keyboard |
|---|---|---|
| `left_command` | `left_option` | Win → Option (overrides profile) |
| `left_option` | `left_control` | Alt → Control |
| `right_command` | `right_option` | Same for right side |
| `right_option` | `right_control` | Same for right side |

Profile-level `left_control → left_command` still applies (not overridden), so Ctrl → Cmd works on both keyboards.

#### Net result on both keyboards

| Physical key | Built-in Mac keyboard | External Windows keyboard |
|---|---|---|
| Ctrl / Ctrl | → Command | → Command |
| Command / Win | → Control (Alt) | → Option (Win) |
| Option / Alt | → Option (Win) | → Control (Alt) |

After these swaps, all **complex rules** below operate on the remapped codes (e.g. Win = `option` in rules on both keyboards).

> **Adding a different external keyboard?** Open Karabiner-Elements → Devices tab to find the new keyboard's vendor/product ID, then add another entry to the `devices` array with the same simple_modifications as the Logitech entry.

### 4.2 Complex rules summary

| # | Rule | What it does | Why needed |
|---|---|---|---|
| 1 | Win+Arrow → Ctrl+Option+Arrow | Window snapping via Rectangle | Win+Arrow and Ctrl+Arrow both map to Option+Arrow; adding Ctrl distinguishes them for Rectangle |
| 2 | Terminal: Ctrl+Arrow → Esc+b/f | Word-by-word nav in terminals | Option+Arrow sends special characters in terminal emulators, not word nav |
| 3 | Ctrl+Arrow → Option+Arrow | Word-by-word cursor movement | macOS uses Option+Arrow for word nav (non-terminal apps) |
| 4 | Terminal Ctrl+C/Z/D/L → Control signals | Sends real SIGINT/suspend/EOF/clear in Ghostty & Terminal.app | Without this, Ctrl+C = Cmd+C = Copy in terminals |
| 5 | Win+1/2/3 → launch apps | Chrome, Ghostty, IPython | Taskbar-style launchers |
| 6 | Media keys → F1–F12 | External keyboard media keys become function keys | External keyboards send consumer_key_code instead of f-key |
| 7 | F11 → Cmd+Ctrl+F | Fullscreen toggle | macOS fullscreen shortcut differs from Windows |
| 8 | Win+D → hide all apps | Show Desktop | Uses osascript to hide all foreground apps, like Windows minimize-all |
| 9 | Cmd+Space → blocked | Prevent physical Ctrl+Space from opening Spotlight | Physical Ctrl maps to Command; this swallows Cmd+Space at source |
| 10 | Alt+Space → Cmd+Space | Open Spotlight | Physical Alt → Control; this converts Control+Space to Cmd+Space (Spotlight) |
| 11 | Alt+Shift (release) → toggle input source | Switch input source (language) | Uses `to_if_alone` to detect release of Alt+Shift, then calls a compiled Swift binary (`toggle-input-source`) that uses the Carbon `TISSelectInputSource` API directly — bypasses symbolic hotkeys entirely for reliable, app-independent switching |
| 12 | Ctrl+Backspace → Option+Backspace | Delete previous word | macOS word-delete uses Option |
| 13 | Cmd+Shift+Esc → Activity Monitor | Task Manager equivalent | — |
| 14 | Terminal: Home/End → Ctrl+A/E | Beginning/end of line in terminals | Cmd+Arrow doesn't map to line nav in shells |
| 15 | Home/End → Cmd+Arrows | Line/Document navigation | macOS defaults to scrolling for Home/End |
| 16 | Win+L → Cmd+Ctrl+Q | Lock screen | macOS lock shortcut differs from Windows |
| 17 | Ctrl+Tab → Cmd+Shift+] | Next/Previous tab | macOS Cmd+Tab is app switcher; AltTab replaces it |
| 18 | Alt+F3 → Option+F3 (VS Code / Antigravity) | Select All Occurrences | Physical Alt → Control; this app-scoped rule sends Option+F3 instead |
| 19 | Win+V → Cmd+Shift+C | Clipboard history (Maccy) | Keeps Maccy's default hotkey while using Win+V |

**Key design decisions:**
- Rule 1 uses `"optional": []` — only fires when Option is the **sole** modifier.
- Rules 2 and 14 (terminal word-nav and Home/End) are placed **before** their generic counterparts (rules 3 and 15). Karabiner is first-match, so the terminal-scoped rules fire first in Ghostty/Terminal.app, and the generic rules handle all other apps.
- Rule 3 uses `"optional": ["shift"]` — allows Ctrl+Shift+Arrow to select by word.
- Rule 4: Ctrl+Shift+C/V entries come **before** Ctrl+C (Karabiner is first-match), so copy/paste still works in terminals via Ctrl+Shift+C/V.
- Rule 6 must be placed **before** rule 7 in the config, so that the media-key volume_decrement → F11 fires first, then F11 → fullscreen fires.
- Rule 8 (Win+D) uses a `shell_command` to hide all foreground apps via osascript, mimicking Windows' minimize-all behavior. Apps can be restored from the Dock or via Alt+Tab.
- Rule 9 blocks Cmd+Space, so physical Ctrl+Space no longer opens Spotlight after the modifier swaps.
- Rule 11 uses a compiled Swift binary (`~/.local/bin/toggle-input-source`) that calls the macOS Carbon `TISSelectInputSource` API directly to switch input sources. This bypasses symbolic hotkeys (Ctrl+Space) entirely, so it works reliably in every app regardless of what keyboard shortcuts the app intercepts. The `to_if_alone` timeout is set to 2000ms (default is 1000ms) to be more forgiving of slightly slow key releases.
- Rule 17 converts Cmd+Tab → Cmd+Shift+] (next tab). This replaces the macOS native app switcher, which AltTab already replaces.
- There is **NO** Karabiner rule for Alt+Tab — AltTab is configured to listen on Control+Tab directly (see Section 6).
- **F11 on built-in MacBook keyboard**: Use Fn+F11 (physical F-key row) or press Ctrl+Cmd+F directly (maps to Cmd+Control+F = macOS fullscreen after simple mods).
- Rule 18 is scoped to VS Code and Antigravity only — in other apps, Alt+F3 still sends Control+F3.

### 4.3 Config file

**Repo path**: `config/karabiner/karabiner.json`
**System location**: `~/.config/karabiner/karabiner.json`

The install script (`./install.sh`) copies this file automatically. To install manually:

```bash
mkdir -p ~/.config/karabiner
cp config/karabiner/karabiner.json ~/.config/karabiner/karabiner.json
```

---

## 5. Rectangle — Window Snapping

Rectangle listens on **Ctrl+Option+Arrow** (modifier flags = 786432) because Karabiner converts Win+Arrow into Ctrl+Option+Arrow to distinguish it from Ctrl+Arrow word navigation.

| Action | keyCode | modifierFlags |
|---|---|---|
| Snap Left | 123 | 786432 |
| Snap Right | 124 | 786432 |
| Maximize | 126 | 786432 |
| Restore (Win+Down) | 125 | 786432 |

### Config file

**Repo path**: `config/rectangle/RectangleConfig.json`

Import via Rectangle UI: **Rectangle → Settings → Import**, then select the file from this repo.

---

## 6. AltTab — Window Switching

AltTab is configured to listen directly on **Control+Tab** (which is what physical Alt+Tab produces after Karabiner simple mods). No Karabiner complex rule is needed — AltTab handles it natively.

This means:
- **Hold Alt, press Tab repeatedly** to cycle through windows
- **Hold Alt, use arrow keys** to navigate the window grid
- **Release Alt** to switch to the selected window

### Settings

These settings are applied automatically by `./install.sh`. The key settings are:

- **Hold modifier**: Control (`⌃`) — because physical Alt maps to Control after Karabiner simple mods. AltTab 10.x stores this in ShortcutRecorder's secure coding format; the install script uses PlistBuddy to merge the exported binary from `config/alttab/holdShortcut.plist`
- **Show minimized/hidden windows**: disabled — only show active windows
- **Menu bar icon**: hidden

> **Why no Karabiner rule?** Previously we had a Karabiner rule converting Control+Tab → Option+Tab. This broke arrow-key navigation because the held modifier (Control) did not match what AltTab expected (Option). By configuring AltTab to directly listen on Control+Tab, the held modifier is genuine and arrow navigation works correctly.

---

## 7. Clipboard History — Maccy (Win+V)

Maccy is a lightweight, open-source clipboard manager. It uses `Cmd+Shift+C` as its default hotkey.

Install:

```bash
brew install --cask maccy
```

Then:

1. Open Maccy once and enable **Launch at Login** in Maccy settings.
2. Optional: If you enable **Paste automatically**, grant Accessibility permission to Maccy (System Settings → Privacy & Security → Accessibility).

Win+V integration is handled by Karabiner rule 19, which maps `Win+V` (Option+V) to `Cmd+Shift+C`, so Maccy opens without changing its own shortcut.

---

## 8. Page Up / Page Down — Cursor Movement

By default, macOS Page Up/Down only scrolls the view without moving the cursor. On Windows, the cursor moves too. This is fixed via a **DefaultKeyBinding.dict** file (works for all Cocoa apps — TextEdit, Safari, Notes, etc.; VS Code already handles this correctly on its own).

**Repo path**: `config/keybindings/DefaultKeyBinding.dict`
**System location**: `~/Library/KeyBindings/DefaultKeyBinding.dict`

The install script (`./install.sh`) copies this file automatically. To install manually:

```bash
mkdir -p ~/Library/KeyBindings
cp config/keybindings/DefaultKeyBinding.dict ~/Library/KeyBindings/DefaultKeyBinding.dict
```

> **Note**: Apps must be restarted after creating/changing this file. A system logout/login is recommended.

> **Why not Karabiner?** Karabiner can only remap keys to other keys/modifiers. On macOS there is no key combination that means "move cursor by page" — it requires changing the Cocoa text system action from `scrollPageUp:` to `pageUp:`, which only DefaultKeyBinding.dict can do.

---

## 9. Red X Button — Quit on Close

By default, macOS's red close button only closes the window — the app keeps running in the Dock. On Windows, clicking X quits the application. **RedQuits** restores this behavior: when you close the last window of an app, it quits the app entirely.

Installed automatically by `./install.sh`, which also adds RedQuits to Login Items. If macOS blocks background items, allow it in System Settings → General → Login Items. No further configuration is needed.

> **Note**: Some macOS apps (e.g. Finder, menu bar apps) intentionally have no windows and are unaffected.

---

## 10. Scroll Direction

macOS "natural scrolling" is inverted compared to Windows for mouse wheels. **UnnaturalScrollWheels** reverses scroll direction for mouse only, keeping trackpad natural scrolling intact.

Installed automatically by `./install.sh`, which also adds it to Login Items. If macOS blocks background items, allow it in System Settings → General → Login Items.

---

## 11. VS Code

Enable Ctrl+scroll zoom (Cmd+scroll after remapping). Add to VS Code `settings.json` (`Cmd+Shift+P` → "Open User Settings JSON"):

```json
{
    "editor.mouseWheelZoom": true
}
```

---

## 12. Keyboard Cheat Sheet

### General Shortcuts

| Windows Shortcut | What Happens |
|---|---|
| Ctrl+C/V/X/Z | Copy/Paste/Cut/Undo |
| Ctrl+Left/Right | Move cursor by word |
| Ctrl+Shift+Left/Right | Select by word |
| Ctrl+Backspace | Delete previous word |
| Win+Left/Right | Snap window left/right |
| Win+Up | Maximize window |
| Win+Down | Restore / De-maximize |
| Alt+Tab (+ arrow keys) | Switch between windows |
| Ctrl+Tab / Ctrl+Shift+Tab | Next / Previous tab |
| Win+D | Show Desktop (hide all apps) |
| Alt+Space | Spotlight search |
| Alt+Shift (press & release) | Switch input source (language) |
| Win+V | Clipboard history (Maccy) |
| F11 | Toggle fullscreen |
| Win+1/2/3 | Open Chrome / Ghostty / IPython |
| Win+L | Lock screen |
| Cmd+Shift+Esc | Activity Monitor (Task Manager) |
| § (on Mac keyboard) | ` (backtick); Shift+§ = ~ (tilde) |
| Home / End | Beginning / End of line |
| Ctrl+Home / End | Beginning / End of document |
| Alt+F3 | Select All Occurrences (VS Code / Antigravity) |
| Page Up / Page Down | Move cursor up/down one page |

### Terminal-Specific (Ghostty / Terminal.app)

| Windows Shortcut | What Happens |
|---|---|
| Ctrl+C | SIGINT (interrupt) |
| Ctrl+Z | Suspend process |
| Ctrl+D | EOF (close shell) |
| Ctrl+L | Clear screen |
| Ctrl+Shift+C | Copy (since Ctrl+C = SIGINT) |
| Ctrl+Shift+V | Paste |
| Ctrl+Left/Right | Move cursor by word |
| Home / End | Beginning / End of line |

---

## 13. Known Limitations

These issues cannot be resolved generically via Karabiner because of architectural constraints:

| Issue | Root Cause | Workaround |
|---|---|---|
| Ctrl+C/R/Z in VS Code / Antigravity terminal | Karabiner can't distinguish terminal panel vs editor within the same app. Physical Ctrl → Cmd, which triggers IDE commands, not terminal control chars. | Configure IDE keybindings: bind Cmd+C → send `\u0003` (SIGINT) when terminal is focused. In VS Code, Alt (physical) sends Control, so **Alt+C/R/Z works** as a fallback. |
| Alt+F3 in other apps (not VS Code / Antigravity) | Physical Alt → Control (for AltTab), but apps expect Option for "Alt" shortcuts. A Karabiner rule now fixes this for VS Code and Antigravity (rule 18). | For other apps: remap in the app's settings, or use the app's native equivalent. |
| Ctrl+scroll zoom in browsers | Karabiner cannot intercept scroll wheel events, only key presses. | Use **Ctrl+= / Ctrl+-** for page zoom (maps to Cmd++/Cmd+-, works in all browsers). |
| F11 on built-in MacBook keyboard | No dedicated F11 key on Touch Bar models. | Press **Fn+F11** (Touch Bar/physical F-row), or **Ctrl+Cmd+F** on built-in keyboard (maps to Cmd+Control+F = fullscreen). |
