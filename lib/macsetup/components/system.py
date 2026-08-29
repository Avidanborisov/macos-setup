"""macOS system defaults: Dock, F-keys, locale, symbolic hotkeys."""

from ..framework import Check, Component, DefaultsSpec
from .. import util

ACTIVATE_SETTINGS = ("/System/Library/PrivateFrameworks/SystemAdministration.framework"
                     "/Resources/activateSettings")


def _hotkey(enabled, params):
    return {
        "enabled": enabled,
        "value": {"parameters": params, "type": "standard"},
    }


# AppleSymbolicHotKeys ids:
#   60 = Select previous input source (Ctrl+Space) — enabled, used to switch language
#   32/33 = Mission Control / App Expose (Ctrl+Up/Down) — disabled so the held
#           AltTab modifier (Control = physical Alt) + arrows reaches AltTab
#   79/80 = move left/right a Space (Ctrl+Left/Right) — disabled, same reason
#   81/82 = same with Shift — disabled
SYMBOLIC_HOTKEYS = {
    "60": _hotkey(True, [32, 49, 262144]),
    "32": _hotkey(False, [65535, 126, 262144]),
    "33": _hotkey(False, [65535, 125, 262144]),
    "79": _hotkey(False, [65535, 123, 262144]),
    "80": _hotkey(False, [65535, 124, 262144]),
    "81": _hotkey(False, [65535, 123, 393216]),
    "82": _hotkey(False, [65535, 124, 393216]),
}


class SystemDefaults(Component):
    name = "system"
    description = "Dock auto-hide, F-keys standard, English locale, trackpad stays natural"

    specs = [
        DefaultsSpec("com.apple.dock", {"autohide": True}),
        DefaultsSpec("NSGlobalDomain", {
            "com.apple.keyboard.fnState": True,   # F-keys act as F-keys
            "AppleLanguages": ["en"],
            "AppleLocale": "en_US",
            "AppleCollationOrder": "en",
            # Trackpad keeps natural scrolling; the mouse wheel is inverted
            # per-device by UnnaturalScrollWheels, NOT by this global toggle.
            "com.apple.swipescrolldirection": True,
        }),
    ]

    def checks(self):
        out = []
        for spec in self.specs:
            out.extend(spec.checks())
        return out

    def apply(self):
        actions = []
        dock_before = util.defaults_export("com.apple.dock").get("autohide")
        for spec in self.specs:
            actions.extend(spec.apply())
        if actions and not util.norm(dock_before):
            util.kill_app("Dock")
            actions.append("restarted Dock")
        return actions


class SymbolicHotkeys(Component):
    name = "hotkeys"
    description = "System keyboard shortcuts (input-source switch on, Ctrl+Arrow shortcuts off)"

    def checks(self):
        live = util.defaults_export("com.apple.symbolichotkeys").get("AppleSymbolicHotKeys", {})
        out = []
        names = {"60": "input-source switch (Ctrl+Space)",
                 "32": "Mission Control (Ctrl+Up)",
                 "33": "App Expose (Ctrl+Down)",
                 "79": "Spaces left (Ctrl+Left)",
                 "80": "Spaces right (Ctrl+Right)",
                 "81": "Spaces left +Shift",
                 "82": "Spaces right +Shift"}
        for key, want in SYMBOLIC_HOTKEYS.items():
            have = live.get(key)
            want_enabled = util.norm(want["enabled"])
            # A missing entry means the macOS default applies; for the ones we
            # disable the default is enabled, so missing == drift.
            have_enabled = util.norm(have.get("enabled")) if isinstance(have, dict) else None
            ok = have_enabled == want_enabled
            out.append(Check(f"hotkey {key} ({names[key]})", ok,
                             "enabled" if want_enabled else "disabled",
                             {1: "enabled", 0: "disabled", None: "not set (macOS default)"}
                             .get(have_enabled, repr(have_enabled))))
        return out

    def apply(self):
        actions = []
        live = util.defaults_export("com.apple.symbolichotkeys").get("AppleSymbolicHotKeys", {})
        changed = False
        for key, want in SYMBOLIC_HOTKEYS.items():
            have = live.get(key)
            have_enabled = util.norm(have.get("enabled")) if isinstance(have, dict) else None
            if have_enabled != util.norm(want["enabled"]):
                util.run(["defaults", "write", "com.apple.symbolichotkeys",
                          "AppleSymbolicHotKeys", "-dict-add", key,
                          _plist_fragment(want)], check=True)
                actions.append(f"set symbolic hotkey {key}")
                changed = True
        if changed:
            util.run([ACTIVATE_SETTINGS, "-u"])
            actions.append("activated settings (activateSettings -u)")
        return actions


def _plist_fragment(value):
    import plistlib
    xml = plistlib.dumps(value).decode()
    return xml[xml.index("<dict>"): xml.rindex("</dict>") + len("</dict>")]


class ZshrcBlock(Component):
    name = "zshrc"
    description = "Managed ~/.zshrc block: Home/End keybindings for the shell, LC_TIME"

    BEGIN = "# >>> macos-setup managed block >>>"
    END = "# <<< macos-setup managed block <<<"

    def _block_body(self):
        lines = [
            "# Home/End move to beginning/end of line (zsh binds neither by default).",
            "# Karabiner passes Home/End through to the terminal; these cover the",
            "# escape-sequence variants Ghostty and tmux emit.",
            "bindkey '^[[H'  beginning-of-line",
            "bindkey '^[OH'  beginning-of-line",
            "bindkey '^[[1~' beginning-of-line",
            "bindkey '^[[F'  end-of-line",
            "bindkey '^[OF'  end-of-line",
            "bindkey '^[[4~' end-of-line",
        ]
        zshrc = util.HOME / ".zshrc"
        text = zshrc.read_text() if zshrc.exists() else ""
        # Only add LC_TIME to the block if it isn't already set elsewhere.
        outside = self._strip_block(text)
        if "LC_TIME" not in outside:
            lines.append("export LC_TIME=en_US.UTF-8")
        return "\n".join([self.BEGIN] + lines + [self.END])

    def _strip_block(self, text):
        if self.BEGIN in text and self.END in text:
            head, rest = text.split(self.BEGIN, 1)
            _, tail = rest.split(self.END, 1)
            return head + tail
        return text

    def _current_block(self, text):
        if self.BEGIN in text and self.END in text:
            rest = text.split(self.BEGIN, 1)[1]
            return self.BEGIN + rest.split(self.END, 1)[0] + self.END
        return None

    def checks(self):
        zshrc = util.HOME / ".zshrc"
        text = zshrc.read_text() if zshrc.exists() else ""
        current = self._current_block(text)
        ok = current == self._block_body()
        return [Check("~/.zshrc managed block", ok, "present and current",
                      "up to date" if ok else
                      ("missing" if current is None else "outdated"))]

    def apply(self):
        zshrc = util.HOME / ".zshrc"
        text = zshrc.read_text() if zshrc.exists() else ""
        if self._current_block(text) == self._block_body():
            return []
        stripped = self._strip_block(text).rstrip("\n")
        new = (stripped + "\n\n" if stripped else "") + self._block_body() + "\n"
        zshrc.write_text(new)
        return ["updated managed block in ~/.zshrc (restart shells to pick up)"]
