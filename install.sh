#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_SUFFIX=".backup.$(date +%Y%m%d%H%M%S)"

backup_and_copy() {
    local src="$1"
    local dest="$2"
    local dest_dir
    dest_dir="$(dirname "$dest")"

    mkdir -p "$dest_dir"

    if [[ -e "$dest" ]]; then
        echo "  Backing up existing: $dest → ${dest}${BACKUP_SUFFIX}"
        cp "$dest" "${dest}${BACKUP_SUFFIX}"
    fi

    cp "$src" "$dest"
    echo "  Installed: $dest"
}

get_app_path() {
    local app_name="$1"
    local app_path=""

    for base in "/Applications" "/Applications/Utilities"; do
        if [[ -d "$base/$app_name.app" ]]; then
            app_path="$base/$app_name.app"
            break
        fi
    done

    if [[ -z "$app_path" ]] && command -v mdfind &>/dev/null; then
        app_path="$(mdfind "kMDItemFSName == '$app_name.app'" | head -n 1)"
    fi

    echo "$app_path"
}

add_login_item() {
    local app_name="$1"
    local app_path
    app_path="$(get_app_path "$app_name")"

    if [[ -z "$app_path" ]]; then
        echo "  - $app_name not found (skipping login item)"
        return
    fi

    local exists
    exists="$(osascript -e "tell application \"System Events\" to if exists login item \"$app_name\" then return \"yes\" else return \"no\"" 2>/dev/null || true)"
    if [[ "$exists" == "yes" ]]; then
        echo "  - $app_name already in Login Items"
        return
    fi

    osascript -e "tell application \"System Events\" to make login item at end with properties {path:\"$app_path\", hidden:false, name:\"$app_name\"}" >/dev/null 2>&1 || true
    echo "  - Added $app_name to Login Items"
}

echo "=== macOS Windows Keyboard Setup — Install ==="
echo ""

# ---- Step 1: Install apps via Homebrew ----
echo "[1/10] Installing apps via Homebrew"
if ! command -v brew &>/dev/null; then
    echo "  Homebrew not found. Install it first:"
    echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
fi
brew install --cask karabiner-elements rectangle alt-tab maccy ghostty unnaturalscrollwheels redquits 2>/dev/null || true
echo "  Apps installed (already-installed apps were skipped)"

# ---- Step 2: macOS system defaults ----
echo "[2/10] Applying macOS system defaults"
defaults write com.apple.dock autohide -bool true
killall Dock 2>/dev/null || true
echo "  Dock: auto-hide enabled"

defaults write -g com.apple.keyboard.fnState -bool true
echo "  F-keys: standard function keys enabled"

defaults write NSGlobalDomain AppleLanguages -array en
defaults write NSGlobalDomain AppleLocale -string en_US
defaults write NSGlobalDomain AppleCollationOrder -string en
killall SystemUIServer 2>/dev/null || true
echo "  Locale: forced to English"

# Enable Input Source switching on Ctrl+Space (used by Win+Space Karabiner rule)
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 60 \
    '<dict><key>enabled</key><true/><key>value</key><dict><key>parameters</key><array><integer>32</integer><integer>49</integer><integer>262144</integer></array><key>type</key><string>standard</string></dict></dict>'
echo "  Keyboard shortcut: Ctrl+Space input source switching enabled"

# Disable Control+Arrow system shortcuts so they don't intercept AltTab arrow navigation.
# After key remapping, the AltTab hold key (Control) + Arrow triggers these macOS shortcuts
# instead of letting AltTab handle arrow-key window navigation.
# 32 = Mission Control (Ctrl+Up), 33 = App Expose (Ctrl+Down),
# 79/80 = Move left/right a space (Ctrl+Left/Right), 81/82 = same with Ctrl+Shift
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 32 \
    '<dict><key>enabled</key><false/><key>value</key><dict><key>parameters</key><array><integer>65535</integer><integer>126</integer><integer>262144</integer></array><key>type</key><string>standard</string></dict></dict>'
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 33 \
    '<dict><key>enabled</key><false/><key>value</key><dict><key>parameters</key><array><integer>65535</integer><integer>125</integer><integer>262144</integer></array><key>type</key><string>standard</string></dict></dict>'
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 79 \
    '<dict><key>enabled</key><false/><key>value</key><dict><key>parameters</key><array><integer>65535</integer><integer>123</integer><integer>262144</integer></array><key>type</key><string>standard</string></dict></dict>'
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 80 \
    '<dict><key>enabled</key><false/><key>value</key><dict><key>parameters</key><array><integer>65535</integer><integer>124</integer><integer>262144</integer></array><key>type</key><string>standard</string></dict></dict>'
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 81 \
    '<dict><key>enabled</key><false/><key>value</key><dict><key>parameters</key><array><integer>65535</integer><integer>123</integer><integer>393216</integer></array><key>type</key><string>standard</string></dict></dict>'
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 82 \
    '<dict><key>enabled</key><false/><key>value</key><dict><key>parameters</key><array><integer>65535</integer><integer>124</integer><integer>393216</integer></array><key>type</key><string>standard</string></dict></dict>'
/System/Library/PrivateFrameworks/SystemAdministration.framework/Resources/activateSettings -u
echo "  Keyboard shortcuts: Ctrl+Arrow (Mission Control, Spaces) disabled for AltTab compatibility"

# ---- Step 3: AltTab settings ----
echo "[3/10] Configuring AltTab"
killall "AltTab" 2>/dev/null && sleep 1
# holdShortcut must be written as a ShortcutRecorder binary (AltTab 10.x).
# We use PlistBuddy to merge the exported plist containing the secureData blob.
ALTTAB_PLIST="$HOME/Library/Preferences/com.lwouis.alt-tab-macos.plist"
/usr/libexec/PlistBuddy -c "Delete :holdShortcut" "$ALTTAB_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :holdShortcut dict" "$ALTTAB_PLIST"
/usr/libexec/PlistBuddy -c "Merge '$SCRIPT_DIR/config/alttab/holdShortcut.plist' :holdShortcut" "$ALTTAB_PLIST"
defaults write com.lwouis.alt-tab-macos showMinimizedWindows -int 0
defaults write com.lwouis.alt-tab-macos showHiddenWindows -int 0
defaults write com.lwouis.alt-tab-macos menubarIconShown -bool false
defaults write com.lwouis.alt-tab-macos arrowKeysEnabled -bool true
echo "  AltTab: hold=Control, arrow keys enabled, hide minimized/hidden, no menu bar icon"

# ---- Step 4: Maccy settings ----
echo "[4/10] Configuring Maccy"
killall "Maccy" 2>/dev/null && sleep 1
defaults write org.p0deje.Maccy KeyboardShortcuts_popup -string '{"carbonKeyCode":9,"carbonModifiers":2048}'
defaults write org.p0deje.Maccy pasteByDefault -bool true
defaults write org.p0deje.Maccy menubarIconShown -bool false
echo "  Maccy: hotkey set to Option+V (Win+V), auto-paste enabled, no menu bar icon"

# ---- Step 5: Compile and install helper binaries ----
echo "[5/10] Compiling helper binaries"
mkdir -p "$HOME/.local/bin"
if command -v swiftc &>/dev/null; then
    swiftc -O "$SCRIPT_DIR/bin/src/toggle-input-source.swift" -o "$HOME/.local/bin/toggle-input-source" 2>/dev/null
    echo "  Compiled and installed: ~/.local/bin/toggle-input-source"
else
    echo "  WARNING: swiftc not found. Install Xcode Command Line Tools:"
    echo "    xcode-select --install"
    echo "  Then re-run this script to compile the input source switcher."
fi

# ---- Step 6: Karabiner config ----
echo "[6/10] Installing Karabiner config"
backup_and_copy "$SCRIPT_DIR/config/karabiner/karabiner.json" \
    "$HOME/.config/karabiner/karabiner.json"

# ---- Step 7: DefaultKeyBinding.dict ----
echo "[7/10] Installing DefaultKeyBinding.dict"
backup_and_copy "$SCRIPT_DIR/config/keybindings/DefaultKeyBinding.dict" \
    "$HOME/Library/KeyBindings/DefaultKeyBinding.dict"

# ---- Step 8: Ghostty config ----
echo "[8/10] Installing Ghostty config"
backup_and_copy "$SCRIPT_DIR/config/ghostty/config" \
    "$HOME/.config/ghostty/config"
if [[ -f "$SCRIPT_DIR/config/ghostty/icon_256x256@2x.png" ]]; then
    backup_and_copy "$SCRIPT_DIR/config/ghostty/icon_256x256@2x.png" \
        "$HOME/.config/ghostty/icon_256x256@2x.png"
fi

# ---- Step 9: Login Items ----
echo "[9/10] Adding apps to Login Items"
add_login_item "Karabiner-Elements"
add_login_item "Rectangle"
add_login_item "AltTab"
add_login_item "Maccy"
add_login_item "UnnaturalScrollWheels"
add_login_item "RedQuits"
add_login_item "Ghostty"

# ---- Step 10: Restart affected apps ----
echo "[10/10] Restarting apps to apply settings"
killall "AltTab" 2>/dev/null; sleep 1
open -a "AltTab" && echo "  AltTab restarted" || echo "  AltTab not running (start it manually)"
open -a "Maccy" && echo "  Maccy started" || echo "  Maccy not running (start it manually)"

echo ""
echo "=== Install complete ==="
echo ""
echo "Manual steps remaining:"
echo "  1. Grant Accessibility permissions (System Settings → Privacy & Security → Accessibility):"
echo "     - Karabiner (karabiner_grabber)"
echo "     - Rectangle"
echo "     - AltTab"
echo "     - Maccy (only if you enable \"Paste automatically\")"
echo "  2. Grant Input Monitoring (System Settings → Privacy & Security → Input Monitoring):"
echo "     - Karabiner (karabiner_grabber, karabiner_observer)"
echo "  3. Import Rectangle config:"
echo "     - Open Rectangle → Settings → Import"
echo "     - Select: $SCRIPT_DIR/config/rectangle/RectangleConfig.json"
echo "  4. VS Code: add \"editor.mouseWheelZoom\": true to settings.json"
echo "  5. Add to ~/.zshrc: export LC_TIME=en_US.UTF-8"
echo "  6. Restart macOS to apply all keyboard shortcut changes"
echo ""
echo "If macOS blocks background items, allow them in System Settings → General → Login Items."
