# macOS with Windows Keyboard — Complete Setup Guide

Configuring macOS (with an external Windows keyboard) to behave like Windows. All config files are included verbatim — copy them to reproduce the setup on a fresh machine.

Based on [this blog post](https://imoskvin.com/blog/macos-like-windows/).

---

## Table of Contents

1. [Install Apps](#1-install-apps)
2. [macOS System Settings](#2-macos-system-settings)
3. [Karabiner-Elements — Key Remapping](#3-karabiner-elements--key-remapping)
4. [Rectangle — Window Snapping](#4-rectangle--window-snapping)
5. [AltTab — Window Switching](#5-alttab--window-switching)
6. [Page Up / Page Down — Cursor Movement](#6-page-up--page-down--cursor-movement)
7. [Red X Button — Quit on Close](#7-red-x-button--quit-on-close)
8. [Scroll Direction](#8-scroll-direction)
9. [VS Code](#9-vs-code)
10. [Keyboard Cheat Sheet](#10-keyboard-cheat-sheet)
11. [Quick Setup Script](#11-quick-setup-script)

---

## 1. Install Apps

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install --cask karabiner-elements   # Key remapping
brew install --cask rectangle            # Window snapping
brew install --cask ghostty              # Terminal emulator
brew install --cask alt-tab              # Alt+Tab window switcher
brew install --cask unnaturalscrollwheels # Reverse mouse scroll only
brew install --cask redquits             # Red X button quits the app (Windows behavior)
```

### Login Items

Add to **System Settings → General → Login Items**:
- Karabiner-Elements
- Rectangle
- AltTab
- UnnaturalScrollWheels
- Ghostty
- RedQuits

### Permissions

**System Settings → Privacy & Security → Accessibility**: Karabiner (karabiner_grabber), Rectangle, AltTab

**System Settings → Privacy & Security → Input Monitoring**: Karabiner (karabiner_grabber, karabiner_observer)

---

## 2. macOS System Settings

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

## 3. Karabiner-Elements — Key Remapping

### 3.1 How it works

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

### 3.2 Complex rules summary

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
| 11 | Win+Space → Ctrl+Space | Switch input source (language) | Physical Win → Option; this converts Option+Space to Ctrl+Space (input switching) |
| 12 | Ctrl+Backspace → Option+Backspace | Delete previous word | macOS word-delete uses Option |
| 13 | Cmd+Shift+Esc → Activity Monitor | Task Manager equivalent | — |
| 14 | Terminal: Home/End → Ctrl+A/E | Beginning/end of line in terminals | Cmd+Arrow doesn't map to line nav in shells |
| 15 | Home/End → Cmd+Arrows | Line/Document navigation | macOS defaults to scrolling for Home/End |
| 16 | Win+L → Cmd+Ctrl+Q | Lock screen | macOS lock shortcut differs from Windows |
| 17 | Ctrl+Tab → Cmd+Shift+] | Next/Previous tab | macOS Cmd+Tab is app switcher; AltTab replaces it |
| 18 | Alt+F3 → Option+F3 (VS Code / Antigravity) | Select All Occurrences | Physical Alt → Control; this app-scoped rule sends Option+F3 instead |

**Key design decisions:**
- Rule 1 uses `"optional": []` — only fires when Option is the **sole** modifier.
- Rules 2 and 11 (terminal word-nav and Home/End) are placed **before** their generic counterparts (rules 3 and 12). Karabiner is first-match, so the terminal-scoped rules fire first in Ghostty/Terminal.app, and the generic rules handle all other apps.
- Rule 3 uses `"optional": ["shift"]` — allows Ctrl+Shift+Arrow to select by word.
- Rule 4: Ctrl+Shift+C/V entries come **before** Ctrl+C (Karabiner is first-match), so copy/paste still works in terminals via Ctrl+Shift+C/V.
- Rule 6 must be placed **before** rule 7 in the config, so that the media-key volume_decrement → F11 fires first, then F11 → fullscreen fires.
- Rule 8 (Win+D) uses a `shell_command` to hide all foreground apps via osascript, mimicking Windows' minimize-all behavior. Apps can be restored from the Dock or via Alt+Tab.
- Rule 9 blocks Cmd+Space, so physical Ctrl+Space no longer opens Spotlight after the modifier swaps.
- Rule 11 maps Win+Space to Ctrl+Space for input source switching (language). This must be placed **after** the Cmd+Space block (rule 9) and Alt+Space Spotlight rule (rule 10) — Karabiner is first-match, and Win+Space uses `option` (not `command` or `control`), so there is no conflict.
- Rule 17 converts Cmd+Tab → Cmd+Shift+] (next tab). This replaces the macOS native app switcher, which AltTab already replaces.
- There is **NO** Karabiner rule for Alt+Tab — AltTab is configured to listen on Control+Tab directly (see Section 5).
- **F11 on built-in MacBook keyboard**: Use Fn+F11 (physical F-key row) or press Ctrl+Cmd+F directly (maps to Cmd+Control+F = macOS fullscreen after simple mods).
- Rule 18 is scoped to VS Code and Antigravity only — in other apps, Alt+F3 still sends Control+F3.

### 3.3 Full config file

**File**: `~/.config/karabiner/karabiner.json`

Copy this file verbatim:

```json
{
    "global": {
        "show_in_menu_bar": false
    },
    "profiles": [
        {
            "complex_modifications": {
                "rules": [
                    {
                        "description": "Win+Arrow snaps windows (for Rectangle)",
                        "manipulators": [
                            { "type": "basic", "from": { "key_code": "left_arrow", "modifiers": { "mandatory": ["option"], "optional": [] } }, "to": [{ "key_code": "left_arrow", "modifiers": ["left_control", "left_option"] }] },
                            { "type": "basic", "from": { "key_code": "right_arrow", "modifiers": { "mandatory": ["option"], "optional": [] } }, "to": [{ "key_code": "right_arrow", "modifiers": ["left_control", "left_option"] }] },
                            { "type": "basic", "from": { "key_code": "up_arrow", "modifiers": { "mandatory": ["option"], "optional": [] } }, "to": [{ "key_code": "up_arrow", "modifiers": ["left_control", "left_option"] }] },
                            { "type": "basic", "from": { "key_code": "down_arrow", "modifiers": { "mandatory": ["option"], "optional": [] } }, "to": [{ "key_code": "down_arrow", "modifiers": ["left_control", "left_option"] }] }
                        ]
                    },
                    {
                        "description": "Terminal: Ctrl+Arrow moves by word (Esc+b / Esc+f)",
                        "manipulators": [
                            { "type": "basic", "from": { "key_code": "left_arrow", "modifiers": { "mandatory": ["command"], "optional": [] } }, "to": [{ "key_code": "escape" }, { "key_code": "b" }], "conditions": [{ "type": "frontmost_application_if", "bundle_identifiers": ["^com\\.mitchellh\\.ghostty$", "^com\\.apple\\.Terminal$"] }] },
                            { "type": "basic", "from": { "key_code": "right_arrow", "modifiers": { "mandatory": ["command"], "optional": [] } }, "to": [{ "key_code": "escape" }, { "key_code": "f" }], "conditions": [{ "type": "frontmost_application_if", "bundle_identifiers": ["^com\\.mitchellh\\.ghostty$", "^com\\.apple\\.Terminal$"] }] }
                        ]
                    },
                    {
                        "description": "Ctrl+Arrow moves by word",
                        "manipulators": [
                            { "type": "basic", "from": { "key_code": "left_arrow", "modifiers": { "mandatory": ["command"], "optional": ["shift"] } }, "to": [{ "key_code": "left_arrow", "modifiers": ["left_option"] }] },
                            { "type": "basic", "from": { "key_code": "right_arrow", "modifiers": { "mandatory": ["command"], "optional": ["shift"] } }, "to": [{ "key_code": "right_arrow", "modifiers": ["left_option"] }] }
                        ]
                    },
                    {
                        "description": "Terminal: Ctrl+C/Z/D/L send real control signals, Ctrl+Shift+C/V for copy/paste",
                        "manipulators": [
                            { "type": "basic", "from": { "key_code": "c", "modifiers": { "mandatory": ["command", "shift"] } }, "to": [{ "key_code": "c", "modifiers": ["left_command"] }], "conditions": [{ "type": "frontmost_application_if", "bundle_identifiers": ["^com\\.mitchellh\\.ghostty$", "^com\\.apple\\.Terminal$"] }] },
                            { "type": "basic", "from": { "key_code": "v", "modifiers": { "mandatory": ["command", "shift"] } }, "to": [{ "key_code": "v", "modifiers": ["left_command"] }], "conditions": [{ "type": "frontmost_application_if", "bundle_identifiers": ["^com\\.mitchellh\\.ghostty$", "^com\\.apple\\.Terminal$"] }] },
                            { "type": "basic", "from": { "key_code": "c", "modifiers": { "mandatory": ["command"], "optional": [] } }, "to": [{ "key_code": "c", "modifiers": ["left_control"] }], "conditions": [{ "type": "frontmost_application_if", "bundle_identifiers": ["^com\\.mitchellh\\.ghostty$", "^com\\.apple\\.Terminal$"] }] },
                            { "type": "basic", "from": { "key_code": "z", "modifiers": { "mandatory": ["command"], "optional": [] } }, "to": [{ "key_code": "z", "modifiers": ["left_control"] }], "conditions": [{ "type": "frontmost_application_if", "bundle_identifiers": ["^com\\.mitchellh\\.ghostty$", "^com\\.apple\\.Terminal$"] }] },
                            { "type": "basic", "from": { "key_code": "d", "modifiers": { "mandatory": ["command"], "optional": [] } }, "to": [{ "key_code": "d", "modifiers": ["left_control"] }], "conditions": [{ "type": "frontmost_application_if", "bundle_identifiers": ["^com\\.mitchellh\\.ghostty$", "^com\\.apple\\.Terminal$"] }] },
                            { "type": "basic", "from": { "key_code": "l", "modifiers": { "mandatory": ["command"], "optional": [] } }, "to": [{ "key_code": "l", "modifiers": ["left_control"] }], "conditions": [{ "type": "frontmost_application_if", "bundle_identifiers": ["^com\\.mitchellh\\.ghostty$", "^com\\.apple\\.Terminal$"] }] }
                        ]
                    },
                    {
                        "description": "Win+1/2/3 launch Chrome, Ghostty, IPython",
                        "manipulators": [
                            { "from": { "key_code": "1", "modifiers": { "mandatory": ["option"], "optional": ["any"] } }, "to": [{ "shell_command": "open -a 'Google Chrome'" }], "type": "basic" },
                            { "from": { "key_code": "2", "modifiers": { "mandatory": ["option"], "optional": ["any"] } }, "to": [{ "shell_command": "open -a 'Ghostty'" }], "type": "basic" },
                            { "from": { "key_code": "3", "modifiers": { "mandatory": ["option"], "optional": ["any"] } }, "to": [{ "shell_command": "open -na 'Ghostty' --args -e /opt/homebrew/bin/ipython" }], "type": "basic" }
                        ]
                    },
                    {
                        "description": "Media keys send F1-F12",
                        "manipulators": [
                            { "type": "basic", "from": { "consumer_key_code": "brightness_down" }, "to": [{ "key_code": "f1" }] },
                            { "type": "basic", "from": { "consumer_key_code": "brightness_up" }, "to": [{ "key_code": "f2" }] },
                            { "type": "basic", "from": { "consumer_key_code": "mission_control" }, "to": [{ "key_code": "f3" }] },
                            { "type": "basic", "from": { "consumer_key_code": "launchpad" }, "to": [{ "key_code": "f4" }] },
                            { "type": "basic", "from": { "consumer_key_code": "illumination_down" }, "to": [{ "key_code": "f5" }] },
                            { "type": "basic", "from": { "consumer_key_code": "illumination_up" }, "to": [{ "key_code": "f6" }] },
                            { "type": "basic", "from": { "consumer_key_code": "rewind" }, "to": [{ "key_code": "f7" }] },
                            { "type": "basic", "from": { "consumer_key_code": "play_or_pause" }, "to": [{ "key_code": "f8" }] },
                            { "type": "basic", "from": { "consumer_key_code": "fastforward" }, "to": [{ "key_code": "f9" }] },
                            { "type": "basic", "from": { "consumer_key_code": "mute" }, "to": [{ "key_code": "f10" }] },
                            { "type": "basic", "from": { "consumer_key_code": "volume_decrement" }, "to": [{ "key_code": "f11" }] },
                            { "type": "basic", "from": { "consumer_key_code": "volume_increment" }, "to": [{ "key_code": "f12" }] }
                        ]
                    },
                    {
                        "description": "F11 triggers fullscreen (Cmd+Ctrl+F)",
                        "manipulators": [
                            { "type": "basic", "from": { "key_code": "f11" }, "to": [{ "key_code": "f", "modifiers": ["left_command", "left_control"] }] }
                        ]
                    },
                    {
                        "description": "Win+D shows desktop (hide all apps)",
                        "manipulators": [
                            { "type": "basic", "from": { "key_code": "d", "modifiers": { "mandatory": ["option"], "optional": [] } }, "to": [{ "shell_command": "osascript -e 'tell application \"System Events\" to set visible of every process whose background only is false to false'" }] }
                        ]
                    },
                    {
                        "description": "Block physical Ctrl+Space (Command+Space after remap)",
                        "manipulators": [
                            { "type": "basic", "from": { "key_code": "spacebar", "modifiers": { "mandatory": ["command"], "optional": [] } }, "to": [{ "key_code": "vk_none" }] }
                        ]
                    },
                    {
                        "description": "Alt+Space opens Spotlight (maps to Cmd+Space)",
                        "manipulators": [
                            { "type": "basic", "from": { "key_code": "spacebar", "modifiers": { "mandatory": ["control"], "optional": [] } }, "to": [{ "key_code": "spacebar", "modifiers": ["left_command"] }] }
                        ]
                    },
                    {
                        "description": "Win+Space switches input source (via Ctrl+Space)",
                        "manipulators": [
                            { "type": "basic", "from": { "key_code": "spacebar", "modifiers": { "mandatory": ["option"], "optional": [] } }, "to": [{ "key_code": "spacebar", "modifiers": ["left_control"] }] }
                        ]
                    },
                    {
                        "description": "Ctrl+Delete deletes previous word",
                        "manipulators": [
                            { "from": { "key_code": "delete_or_backspace", "modifiers": { "mandatory": ["left_command"], "optional": ["shift"] } }, "to": [{ "key_code": "delete_or_backspace", "modifiers": ["left_option"] }], "type": "basic" }
                        ]
                    },
                    {
                        "description": "Cmd+Shift+Esc opens Activity Monitor",
                        "manipulators": [
                            { "from": { "key_code": "escape", "modifiers": { "mandatory": ["command", "shift"] } }, "to": [{ "shell_command": "open -a 'Activity Monitor.app'" }], "type": "basic" }
                        ]
                    },
                    {
                        "description": "Terminal: Home/End go to beginning/end of line (Ctrl+A / Ctrl+E)",
                        "manipulators": [
                            { "type": "basic", "from": { "key_code": "home", "modifiers": { "optional": ["shift"] } }, "to": [{ "key_code": "a", "modifiers": ["left_control"] }], "conditions": [{ "type": "frontmost_application_if", "bundle_identifiers": ["^com\\.mitchellh\\.ghostty$", "^com\\.apple\\.Terminal$"] }] },
                            { "type": "basic", "from": { "key_code": "end", "modifiers": { "optional": ["shift"] } }, "to": [{ "key_code": "e", "modifiers": ["left_control"] }], "conditions": [{ "type": "frontmost_application_if", "bundle_identifiers": ["^com\\.mitchellh\\.ghostty$", "^com\\.apple\\.Terminal$"] }] }
                        ]
                    },
                    {
                        "description": "Home/End keys behave like Windows (Line/Document navigation)",
                        "manipulators": [
                            { "from": { "key_code": "home", "modifiers": { "mandatory": ["command"], "optional": ["shift"] } }, "to": [{ "key_code": "up_arrow", "modifiers": ["left_command"] }], "type": "basic" },
                            { "from": { "key_code": "end", "modifiers": { "mandatory": ["command"], "optional": ["shift"] } }, "to": [{ "key_code": "down_arrow", "modifiers": ["left_command"] }], "type": "basic" },
                            { "from": { "key_code": "home", "modifiers": { "optional": ["shift"] } }, "to": [{ "key_code": "left_arrow", "modifiers": ["left_command"] }], "type": "basic" },
                            { "from": { "key_code": "end", "modifiers": { "optional": ["shift"] } }, "to": [{ "key_code": "right_arrow", "modifiers": ["left_command"] }], "type": "basic" }
                        ]
                    },
                    {
                        "description": "Win+L locks screen",
                        "manipulators": [
                            {
                                "from": { "key_code": "l", "modifiers": { "mandatory": ["option"], "optional": [] } },
                                "to": [{ "key_code": "q", "modifiers": ["left_command", "left_control"] }],
                                "type": "basic"
                            }
                        ]
                    },
                    {
                        "description": "Ctrl+Tab / Ctrl+Shift+Tab switches tabs",
                        "manipulators": [
                            { "type": "basic", "from": { "key_code": "tab", "modifiers": { "mandatory": ["command"], "optional": [] } }, "to": [{ "key_code": "close_bracket", "modifiers": ["left_command", "left_shift"] }] },
                            { "type": "basic", "from": { "key_code": "tab", "modifiers": { "mandatory": ["command", "shift"], "optional": [] } }, "to": [{ "key_code": "open_bracket", "modifiers": ["left_command", "left_shift"] }] }
                        ]
                    },
                    {
                        "description": "Alt+F3 → Option+F3 in VS Code / Antigravity (Select All Occurrences)",
                        "manipulators": [
                            { "type": "basic", "from": { "key_code": "f3", "modifiers": { "mandatory": ["control"], "optional": [] } }, "to": [{ "key_code": "f3", "modifiers": ["left_option"] }], "conditions": [{ "type": "frontmost_application_if", "bundle_identifiers": ["^com\\.microsoft\\.VSCode$", "^com\\.google\\.antigravity$"] }] }
                        ]
                    }
                ]
            },
            "name": "Default profile",
            "selected": true,
            "simple_modifications": [
                { "from": { "key_code": "left_control" }, "to": [{ "key_code": "left_command" }] },
                { "from": { "key_code": "left_command" }, "to": [{ "key_code": "left_control" }] },
                { "from": { "key_code": "right_control" }, "to": [{ "key_code": "right_command" }] },
                { "from": { "key_code": "right_command" }, "to": [{ "key_code": "right_control" }] },
                { "from": { "key_code": "non_us_backslash" }, "to": [{ "key_code": "grave_accent_and_tilde" }] }
            ],
            "devices": [
                {
                    "identifiers": {
                        "is_keyboard": true,
                        "product_id": 50475,
                        "vendor_id": 1133
                    },
                    "simple_modifications": [
                        { "from": { "key_code": "left_command" }, "to": [{ "key_code": "left_option" }] },
                        { "from": { "key_code": "left_option" }, "to": [{ "key_code": "left_control" }] },
                        { "from": { "key_code": "right_command" }, "to": [{ "key_code": "right_option" }] },
                        { "from": { "key_code": "right_option" }, "to": [{ "key_code": "right_control" }] }
                    ]
                }
            ],
            "virtual_hid_keyboard": { "keyboard_type_v2": "ansi" }
        }
    ]
}
```

---

## 4. Rectangle — Window Snapping

Rectangle listens on **Ctrl+Option+Arrow** (modifier flags = 786432) because Karabiner converts Win+Arrow into Ctrl+Option+Arrow to distinguish it from Ctrl+Arrow word navigation.

| Action | keyCode | modifierFlags |
|---|---|---|
| Snap Left | 123 | 786432 |
| Snap Right | 124 | 786432 |
| Maximize | 126 | 786432 |
| Restore (Win+Down) | 125 | 786432 |

### Config file

Save as `~/Documents/RectangleConfig.json`, then import via **Rectangle → Settings → Import**:

```json
{
  "bundleId" : "com.knollsoft.Rectangle",
  "defaults" : {
    "SUEnableAutomaticChecks" : { "bool" : true },
    "allowAnyShortcut" : { "bool" : true },
    "launchOnLogin" : { "bool" : true },
    "hideMenubarIcon" : { "bool" : true },
    "windowSnapping" : { "int" : 0 }
  },
  "shortcuts" : {
    "leftHalf" : { "keyCode" : 123, "modifierFlags" : 786432 },
    "rightHalf" : { "keyCode" : 124, "modifierFlags" : 786432 },
    "maximize" : { "keyCode" : 126, "modifierFlags" : 786432 },
    "restore" : { "keyCode" : 125, "modifierFlags" : 786432 }
  },
  "version" : "99"
}
```

---

## 5. AltTab — Window Switching

AltTab is configured to listen directly on **Control+Tab** (which is what physical Alt+Tab produces after Karabiner simple mods). No Karabiner complex rule is needed — AltTab handles it natively.

This means:
- **Hold Alt, press Tab repeatedly** to cycle through windows
- **Hold Alt, use arrow keys** to navigate the window grid
- **Release Alt** to switch to the selected window

### Settings (applied via defaults)

```bash
# Use Control as the hold modifier (physical Alt = Control after simple mods)
defaults write com.lwouis.alt-tab-macos holdShortcut -string "⌃"

# Only show active windows (hide minimized and hidden)
defaults write com.lwouis.alt-tab-macos showMinimizedWindows -int 0
defaults write com.lwouis.alt-tab-macos showHiddenWindows -int 0

# Hide menu bar icon
defaults write com.lwouis.alt-tab-macos menubarIconShown -bool false

# Restart AltTab to apply
killall "AltTab" 2>/dev/null; sleep 1; open -a "AltTab"
```

> **Why no Karabiner rule?** Previously we had a Karabiner rule converting Control+Tab → Option+Tab. This broke arrow-key navigation because the held modifier (Control) did not match what AltTab expected (Option). By configuring AltTab to directly listen on Control+Tab, the held modifier is genuine and arrow navigation works correctly.

---

## 6. Page Up / Page Down — Cursor Movement

By default, macOS Page Up/Down only scrolls the view without moving the cursor. On Windows, the cursor moves too. This is fixed via a **DefaultKeyBinding.dict** file (works for all Cocoa apps — TextEdit, Safari, Notes, etc.; VS Code already handles this correctly on its own).

**File**: `~/Library/KeyBindings/DefaultKeyBinding.dict`

```
{
    /* Page Up/Down: move cursor instead of just scrolling (Windows behavior) */
    "\UF72C" = "pageUp:";
    "\UF72D" = "pageDown:";

    /* Shift+Page Up/Down: select while paging */
    "$\UF72C" = "pageUpAndModifySelection:";
    "$\UF72D" = "pageDownAndModifySelection:";
}
```

> **Note**: Apps must be restarted after creating/changing this file. A system logout/login is recommended.

> **Why not Karabiner?** Karabiner can only remap keys to other keys/modifiers. On macOS there is no key combination that means "move cursor by page" — it requires changing the Cocoa text system action from `scrollPageUp:` to `pageUp:`, which only DefaultKeyBinding.dict can do.

---

## 8. Red X Button — Quit on Close

By default, macOS's red close button only closes the window — the app keeps running in the Dock. On Windows, clicking X quits the application. **RedQuits** restores this behavior: when you close the last window of an app, it quits the app entirely.

```bash
brew install --cask redquits
```

Add RedQuits to **System Settings → General → Login Items** so it runs on startup. No further configuration is needed.

> **Note**: Some macOS apps (e.g. Finder, menu bar apps) intentionally have no windows and are unaffected.

---

## 8. Scroll Direction

macOS "natural scrolling" is inverted compared to Windows for mouse wheels:

```bash
brew install --cask unnaturalscrollwheels
```

Reverses scroll direction for mouse only, keeping trackpad natural scrolling intact. Add to Login Items.

---

## 9. VS Code

Enable Ctrl+scroll zoom (Cmd+scroll after remapping). Add to VS Code `settings.json` (`Cmd+Shift+P` → "Open User Settings JSON"):

```json
{
    "editor.mouseWheelZoom": true
}
```

---

## 10. Keyboard Cheat Sheet

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
| Win+Space | Switch input source (language) |
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

## Known Limitations

These issues cannot be resolved generically via Karabiner because of architectural constraints:

| Issue | Root Cause | Workaround |
|---|---|---|
| Ctrl+C/R/Z in VS Code / Antigravity terminal | Karabiner can't distinguish terminal panel vs editor within the same app. Physical Ctrl → Cmd, which triggers IDE commands, not terminal control chars. | Configure IDE keybindings: bind Cmd+C → send `\u0003` (SIGINT) when terminal is focused. In VS Code, Alt (physical) sends Control, so **Alt+C/R/Z works** as a fallback. |
| Alt+F3 in other apps (not VS Code / Antigravity) | Physical Alt → Control (for AltTab), but apps expect Option for "Alt" shortcuts. A Karabiner rule now fixes this for VS Code and Antigravity (rule 18). | For other apps: remap in the app's settings, or use the app's native equivalent. |
| Ctrl+scroll zoom in browsers | Karabiner cannot intercept scroll wheel events, only key presses. | Use **Ctrl+= / Ctrl+-** for page zoom (maps to Cmd++/Cmd+-, works in all browsers). |
| F11 on built-in MacBook keyboard | No dedicated F11 key on Touch Bar models. | Press **Fn+F11** (Touch Bar/physical F-row), or **Ctrl+Cmd+F** on built-in keyboard (maps to Cmd+Control+F = fullscreen). |

---

## 11. Quick Setup Script

Run on a fresh macOS machine after installing Homebrew:

```bash
#!/bin/bash
set -e

# --- Install apps ---
brew install --cask karabiner-elements rectangle alt-tab unnaturalscrollwheels redquits

# --- macOS settings ---
defaults write com.apple.dock autohide -bool true && killall Dock
defaults write -g com.apple.keyboard.fnState -bool true
defaults write NSGlobalDomain AppleLanguages -array en
defaults write NSGlobalDomain AppleLocale -string en_US
defaults write NSGlobalDomain AppleCollationOrder -string en
killall SystemUIServer 2>/dev/null || true

# --- AltTab settings ---
defaults write com.lwouis.alt-tab-macos holdShortcut -string "⌃"
defaults write com.lwouis.alt-tab-macos showMinimizedWindows -int 0
defaults write com.lwouis.alt-tab-macos showHiddenWindows -int 0
defaults write com.lwouis.alt-tab-macos menubarIconShown -bool false

# --- Karabiner config ---
mkdir -p ~/.config/karabiner
# Copy the karabiner.json from Section 3.3 above to ~/.config/karabiner/karabiner.json

# --- DefaultKeyBinding.dict (Page Up/Down cursor movement) ---
mkdir -p ~/Library/KeyBindings
cat > ~/Library/KeyBindings/DefaultKeyBinding.dict << 'KEYBIND'
{
    "\UF72C" = "pageUp:";
    "\UF72D" = "pageDown:";
    "$\UF72C" = "pageUpAndModifySelection:";
    "$\UF72D" = "pageDownAndModifySelection:";
}
KEYBIND

# --- Rectangle config ---
# Save the RectangleConfig.json from Section 4 above to ~/Documents/RectangleConfig.json
# Then import: open Rectangle → Settings → Import

echo ""
echo "Done! Manual steps remaining:"
echo "  1. Grant Accessibility: Karabiner, Rectangle, AltTab"
echo "  2. Grant Input Monitoring: Karabiner"
echo "  3. Add to Login Items: Karabiner, Rectangle, AltTab, UnnaturalScrollWheels, RedQuits"
echo "  4. Import Rectangle config: Rectangle → Settings → Import → ~/Documents/RectangleConfig.json"
echo "  5. Restart to apply keyboard shortcut changes (Spotlight)"
echo "  6. Restart AltTab: killall AltTab; open -a AltTab"
echo "  7. VS Code: add editor.mouseWheelZoom: true to settings.json"
```
