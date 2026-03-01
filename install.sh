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

echo "=== macOS Windows Keyboard Setup — Install ==="
echo ""

# Karabiner
echo "[1/4] Karabiner config"
backup_and_copy "$SCRIPT_DIR/config/karabiner/karabiner.json" \
    "$HOME/.config/karabiner/karabiner.json"

# DefaultKeyBinding.dict
echo "[2/4] DefaultKeyBinding.dict"
backup_and_copy "$SCRIPT_DIR/config/keybindings/DefaultKeyBinding.dict" \
    "$HOME/Library/KeyBindings/DefaultKeyBinding.dict"

# Ghostty
echo "[3/4] Ghostty config"
backup_and_copy "$SCRIPT_DIR/config/ghostty/config" \
    "$HOME/.config/ghostty/config"
backup_and_copy "$SCRIPT_DIR/config/ghostty/icon_256x256@2x.png" \
    "$HOME/.config/ghostty/icon_256x256@2x.png"

# macOS defaults
echo "[4/4] macOS keyboard shortcut defaults"
# Disable Input Source switching on Ctrl+Space
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 60 \
  '<dict><key>enabled</key><false/><key>value</key><dict><key>parameters</key><array><integer>32</integer><integer>49</integer><integer>262144</integer></array><key>type</key><string>standard</string></dict></dict>'
echo "  Disabled Ctrl+Space input source switching"

# Apply changes
/System/Library/PrivateFrameworks/SystemAdministration.framework/Resources/activateSettings -u
echo "  Applied defaults changes"

echo ""
echo "Done! Manual steps remaining:"
echo "  1. Install apps: brew install --cask karabiner-elements rectangle alt-tab ghostty unnaturalscrollwheels"
echo "  2. Grant Accessibility: Karabiner, Rectangle, AltTab"
echo "  3. Grant Input Monitoring: Karabiner"
echo "  4. Add to Login Items: Karabiner, Rectangle, AltTab, UnnaturalScrollWheels"
echo "  5. Import Rectangle config: Rectangle → Settings → Import → config/rectangle/RectangleConfig.json"
echo "  6. Restart to apply keyboard shortcut changes"
echo "  7. Restart AltTab: killall AltTab; open -a AltTab"
echo "  8. VS Code: add editor.mouseWheelZoom: true to settings.json"
