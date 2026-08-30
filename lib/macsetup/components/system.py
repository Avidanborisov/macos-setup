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
#   60 = Select previous input source (Ctrl+Space) — DISABLED: language is
#        switched by Karabiner's select_input_source (Alt+Shift), and leaving
#        it on would swallow the Ctrl+Space we send VS Code for autocomplete
#   36 = Show Desktop — rebound from F11 to F17 (keycode 64) and used by the
#        Win+D rule; on F11 it would fire from external-keyboard media keys
#   32/33 = Mission Control / App Expose (Ctrl+Up/Down) — disabled so the held
#           AltTab modifier (Control = physical Alt) + arrows reaches AltTab
#   79/80 = move left/right a Space (Ctrl+Left/Right) — disabled, same reason
#   81/82 = same with Shift — disabled
SYMBOLIC_HOTKEYS = {
    "60": _hotkey(False, [32, 49, 262144]),
    "36": _hotkey(True, [65535, 64, 0]),
    "32": _hotkey(False, [65535, 126, 262144]),
    "33": _hotkey(False, [65535, 125, 262144]),
    "79": _hotkey(False, [65535, 123, 262144]),
    "80": _hotkey(False, [65535, 124, 262144]),
    "81": _hotkey(False, [65535, 123, 393216]),
    "82": _hotkey(False, [65535, 124, 393216]),
}


class SystemDefaults(Component):
    name = "system"
    description = "F-keys standard, English locale, trackpad stays natural"

    specs = [
        # Screenshots go to the clipboard, never to files on the Desktop.
        # Both our shortcuts use the Control variants (Cmd+Ctrl+Shift+4 and
        # Cmd+Ctrl+Shift+3), which always copy regardless of this setting;
        # pinning it keeps any other screenshot shortcut consistent too.
        DefaultsSpec("com.apple.screencapture", {"target": "clipboard"}),
        DefaultsSpec("NSGlobalDomain", {
            "com.apple.keyboard.fnState": True,   # F-keys act as F-keys
            "AppleLanguages": ["en"],
            "AppleLocale": "en_US",
            "AppleCollationOrder": "en",
            # Trackpad keeps natural scrolling; the mouse wheel is inverted
            # per-device by UnnaturalScrollWheels, NOT by this global toggle.
            "com.apple.swipescrolldirection": True,
            # Snappier window zoom/resize animations (maximize, restore,
            # Rectangle snapping). Kept non-zero so motion stays visible.
            "NSWindowResizeTime": 0.05,
            # Global menu-item shortcuts for Format > Text > Writing Direction
            # ("Paragraph" items match first). Karabiner sends these chords on
            # a Ctrl+LeftShift / Ctrl+RightShift tap, like Windows. The
            # makeBaseWritingDirection* selectors can't be used from
            # DefaultKeyBinding.dict — they take the direction from the
            # sender's tag, which key bindings don't have (verified).
            "NSUserKeyEquivalents": {
                "Left to Right": "@~^l",
                "Right to Left": "@~^r",
            },
        }),
    ]

    def checks(self):
        out = []
        for spec in self.specs:
            out.extend(spec.checks())
        return out

    def apply(self):
        actions = []
        for spec in self.specs:
            actions.extend(spec.apply())
        return actions


class InputSources(Component):
    name = "input"
    description = "Keyboard layouts: English (ABC) + Hebrew enabled, toggled with Alt+Shift"

    DOMAIN = "com.apple.HIToolbox"
    KEY = "AppleEnabledInputSources"
    LAYOUTS = [
        {"InputSourceKind": "Keyboard Layout",
         "KeyboardLayout ID": 252, "KeyboardLayout Name": "ABC"},
        {"InputSourceKind": "Keyboard Layout",
         "KeyboardLayout ID": -18432, "KeyboardLayout Name": "Hebrew"},
    ]

    def _enabled(self):
        return util.defaults_export(self.DOMAIN).get(self.KEY, [])

    def _missing(self):
        have = {e.get("KeyboardLayout Name") for e in self._enabled()
                if isinstance(e, dict)}
        return [lay for lay in self.LAYOUTS
                if lay["KeyboardLayout Name"] not in have]

    def checks(self):
        missing = self._missing()
        return [Check("keyboard layouts enabled", not missing,
                      "ABC + Hebrew",
                      "both enabled" if not missing else
                      "missing: " + ", ".join(l["KeyboardLayout Name"] for l in missing))]

    def apply(self):
        missing = self._missing()
        if not missing:
            return []
        util.defaults_write(self.DOMAIN, self.KEY, self._enabled() + missing)
        return ["enabled keyboard layout(s): "
                + ", ".join(l["KeyboardLayout Name"] for l in missing)
                + " (log out/in to take effect)"]


class Dock(Component):
    name = "dock"
    description = "Windows-taskbar-style Dock: instant reveal on any display, minimize into app icon"

    # A pinned Dock only exists on ONE display (macOS limitation — it migrates
    # when summoned at another screen's bottom edge, i.e. "disappears").
    # Auto-hide is the only native way to have it usable on every display, so
    # make the reveal instant instead of the sluggish default.
    spec = DefaultsSpec("com.apple.dock", {
        "autohide": True,
        "autohide-delay": 0.15,            # slight pause before revealing (avoids twitchy pops)
        "autohide-time-modifier": 0.4,     # quick but visible slide animation
        # tilesize is deliberately unmanaged — resize the Dock by hand to taste
        "magnification": False,            # Windows doesn't zoom taskbar icons
        "show-recents": False,             # only pinned + running apps
        "minimize-to-application": True,   # minimized windows go into the app
                                           # icon, not separate tiles on the right
                                           # (macOS ignores this for Finder)
        "mineffect": "scale",              # scale is much faster than genie
        "launchanim": False,               # no bouncing icon on launch
    })

    def checks(self):
        return self.spec.checks()

    def apply(self):
        actions = self.spec.apply()
        if actions:
            util.kill_app("Dock")  # the Dock relaunches itself
            actions.append("restarted Dock")
        return actions


class SymbolicHotkeys(Component):
    name = "hotkeys"
    description = "System keyboard shortcuts (input-source switch on, Ctrl+Arrow shortcuts off)"

    NAMES = {"60": "input-source switch (Ctrl+Space)",
             "36": "Show Desktop (F17, used by Win+D)",
             "32": "Mission Control (Ctrl+Up)",
             "33": "App Expose (Ctrl+Down)",
             "79": "Spaces left (Ctrl+Left)",
             "80": "Spaces right (Ctrl+Right)",
             "81": "Spaces left +Shift",
             "82": "Spaces right +Shift"}

    @staticmethod
    def _matches(have, want):
        if not isinstance(have, dict):
            # A missing entry means the macOS default applies; treat as drift.
            return False
        if util.norm(have.get("enabled")) != util.norm(want["enabled"]):
            return False
        if util.norm(want["enabled"]):
            # For enabled hotkeys the key binding itself must match too.
            params = (have.get("value") or {}).get("parameters")
            return util.norm(params) == util.norm(want["value"]["parameters"])
        return True

    def checks(self):
        live = util.defaults_export("com.apple.symbolichotkeys").get("AppleSymbolicHotKeys", {})
        out = []
        for key, want in SYMBOLIC_HOTKEYS.items():
            have = live.get(key)
            ok = self._matches(have, want)
            want_desc = ("enabled " + repr(want["value"]["parameters"])
                         if util.norm(want["enabled"]) else "disabled")
            if not isinstance(have, dict):
                have_desc = "not set (macOS default)"
            elif util.norm(have.get("enabled")):
                have_desc = "enabled " + repr(util.norm((have.get("value") or {}).get("parameters")))
            else:
                have_desc = "disabled"
            out.append(Check(f"hotkey {key} ({self.NAMES[key]})", ok, want_desc, have_desc))
        return out

    def apply(self):
        actions = []
        live = util.defaults_export("com.apple.symbolichotkeys").get("AppleSymbolicHotKeys", {})
        changed = False
        for key, want in SYMBOLIC_HOTKEYS.items():
            if not self._matches(live.get(key), want):
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
