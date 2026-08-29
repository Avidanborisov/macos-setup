"""Per-app configuration: AltTab, Maccy, Rectangle, UnnaturalScrollWheels, login items."""

import json
import plistlib
import sqlite3
import time
from pathlib import Path

from ..framework import Check, Component, DefaultsSpec, Warning_
from .. import util

PLISTBUDDY = "/usr/libexec/PlistBuddy"


def _restart(app_name):
    util.kill_app(app_name)
    time.sleep(1)
    util.open_app(app_name)


# ---------------------------------------------------------------------------
# AltTab
# ---------------------------------------------------------------------------

class AltTab(Component):
    name = "alttab"
    description = "AltTab: hold Control (= physical Alt), arrow-key navigation"
    manual = ["Grant Accessibility to AltTab"]

    DOMAIN = "com.lwouis.alt-tab-macos"
    spec = DefaultsSpec(DOMAIN, {
        # Show minimized windows like the Windows Alt+Tab does — Win+Down can
        # minimize, and Alt+Tab must be able to bring those windows back.
        "showMinimizedWindows": 1,
        "showHiddenWindows": 0,
        "menubarIconShown": False,
        "arrowKeysEnabled": True,
    })
    HOLD_PLIST = util.CONFIG / "alttab" / "holdShortcut.plist"

    def _hold_ok(self, live):
        # AltTab 10.x stores the hold shortcut as a ShortcutRecorder
        # secure-coded blob; compare against the exported repo copy.
        want = plistlib.loads(self.HOLD_PLIST.read_bytes())
        return util.norm(live.get("holdShortcut")) == util.norm(want)

    def checks(self):
        live = util.defaults_export(self.DOMAIN)
        out = self.spec.checks()
        out.append(Check("holdShortcut is Control", self._hold_ok(live),
                         "ShortcutRecorder blob from repo",
                         "matches" if self._hold_ok(live) else "differs"))
        out.append(Check("AltTab running", util.process_running("AltTab"),
                         "running", "running" if util.process_running("AltTab") else "not running"))
        return out

    def apply(self):
        actions = []
        live = util.defaults_export(self.DOMAIN)
        changed = False
        if not self._hold_ok(live):
            util.kill_app("AltTab")
            time.sleep(1)
            plist = util.HOME / "Library/Preferences" / f"{self.DOMAIN}.plist"
            util.run([PLISTBUDDY, "-c", "Delete :holdShortcut", str(plist)])
            util.run([PLISTBUDDY, "-c", "Add :holdShortcut dict", str(plist)], check=True)
            util.run([PLISTBUDDY, "-c", f"Merge '{self.HOLD_PLIST}' :holdShortcut",
                      str(plist)], check=True)
            actions.append("wrote AltTab holdShortcut (Control)")
            changed = True
        actions.extend(self.spec.apply())
        if changed or actions or not util.process_running("AltTab"):
            _restart("AltTab")
            actions.append("restarted AltTab")
        return actions


# ---------------------------------------------------------------------------
# Maccy
# ---------------------------------------------------------------------------

class Maccy(Component):
    name = "maccy"
    description = "Maccy clipboard history on Win+V (Option+V after remap)"
    manual = ["Grant Accessibility to Maccy (needed for paste-on-select)"]

    DOMAIN = "org.p0deje.Maccy"
    # carbonKeyCode 9 = V, carbonModifiers 2048 = Option -> physical Win+V
    spec = DefaultsSpec(DOMAIN, {
        "KeyboardShortcuts_popup": '{"carbonKeyCode":9,"carbonModifiers":2048}',
        "pasteByDefault": True,
        "menubarIconShown": False,
    })

    def checks(self):
        out = self.spec.checks()
        running = util.process_running("Maccy")
        out.append(Check("Maccy running", running, "running",
                         "running" if running else "not running"))
        return out

    def apply(self):
        actions = self.spec.apply()
        if actions:
            _restart("Maccy")
            actions.append("restarted Maccy")
        elif not util.process_running("Maccy"):
            util.open_app("Maccy")
            actions.append("started Maccy")
        return actions


# ---------------------------------------------------------------------------
# Rectangle
# ---------------------------------------------------------------------------

class Rectangle(Component):
    name = "rectangle"
    description = "Rectangle window snapping on Ctrl+Option+Arrow (= physical Win+Arrow)"
    manual = ["Grant Accessibility to Rectangle"]

    DOMAIN = "com.knollsoft.Rectangle"
    EXPORT = util.CONFIG / "rectangle" / "RectangleConfig.json"

    def _desired(self):
        """Flatten RectangleConfig.json (an export) into defaults keys."""
        cfg = json.loads(self.EXPORT.read_text())
        desired = {}
        for key, spec in cfg.get("defaults", {}).items():
            if not spec:  # empty dicts in the export mean "unset"
                continue
            (typ, value), = spec.items()
            if typ == "bool":
                desired[key] = bool(value)
            elif typ == "int":
                desired[key] = int(value)
            elif typ == "float":
                desired[key] = float(value)
            else:
                desired[key] = value
        for action, sc in cfg.get("shortcuts", {}).items():
            desired[action] = {"keyCode": sc["keyCode"],
                               "modifierFlags": sc["modifierFlags"]}
        return desired

    def checks(self):
        live = util.defaults_export(self.DOMAIN)
        desired = self._desired()
        bad = [k for k, v in desired.items()
               if util.norm(live.get(k)) != util.norm(v)]
        out = [Check("Rectangle settings + shortcuts", not bad,
                     f"{len(desired)} keys from RectangleConfig.json",
                     "all match" if not bad else "drifted: " + ", ".join(sorted(bad)[:8])
                     + ("…" if len(bad) > 8 else ""))]
        running = util.process_running("Rectangle")
        out.append(Check("Rectangle running", running, "running",
                         "running" if running else "not running"))
        return out

    def apply(self):
        live = util.defaults_export(self.DOMAIN)
        desired = self._desired()
        actions = []
        for key, value in desired.items():
            if util.norm(live.get(key)) != util.norm(value):
                util.defaults_write(self.DOMAIN, key, value)
                actions.append(f"set Rectangle {key}")
        if actions:
            _restart("Rectangle")
            actions.append("restarted Rectangle")
        elif not util.process_running("Rectangle"):
            util.open_app("Rectangle")
            actions.append("started Rectangle")
        return actions


# ---------------------------------------------------------------------------
# UnnaturalScrollWheels (mouse wheel inversion; trackpad stays natural)
# ---------------------------------------------------------------------------

class ScrollWheels(Component):
    name = "scroll"
    description = "UnnaturalScrollWheels: invert mouse wheel only (Windows direction)"

    DOMAIN = "com.theron.UnnaturalScrollWheels"
    spec = DefaultsSpec(DOMAIN, {
        "InvertVerticalScroll": True,
        "InvertHorizontalScroll": True,
        "DisableScrollAccel": True,
        "ScrollLines": 3,
    })

    def checks(self):
        out = self.spec.checks()
        running = util.process_running("UnnaturalScrollWheels")
        out.append(Check("UnnaturalScrollWheels running", running, "running",
                         "running" if running else "not running"))
        return out

    def apply(self):
        actions = self.spec.apply()
        if actions:
            _restart("UnnaturalScrollWheels")
            actions.append("restarted UnnaturalScrollWheels")
        elif not util.process_running("UnnaturalScrollWheels"):
            util.open_app("UnnaturalScrollWheels")
            actions.append("started UnnaturalScrollWheels")
        return actions

    def warnings(self):
        out = []
        # Logi Options+ can also manage the mouse wheel; if its per-device
        # scroll direction is set to inverted, the wheel gets double-flipped.
        db = util.HOME / "Library/Application Support/LogiOptionsPlus/settings.db"
        if db.exists():
            try:
                con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
                blob = con.execute(
                    "select file from data order by _id desc limit 1").fetchone()[0]
                con.close()
                settings = json.loads(blob)
                dirs = _find_scroll_dirs(settings)
                for path, d in dirs:
                    if d != "STANDARD":
                        out.append(Warning_(
                            "Logi Options+ inverts the scroll wheel",
                            f"{path} = {d}; UnnaturalScrollWheels already inverts it "
                            "(double inversion)",
                            fix="in Logi Options+, set the mouse scroll direction to Standard"))
            except Exception:
                pass
        return out


def _find_scroll_dirs(obj, path=""):
    found = []
    if isinstance(obj, dict):
        if "mouseScrollWheelSettings" in obj:
            d = obj["mouseScrollWheelSettings"].get("dir")
            if d:
                found.append((path or "profile", d))
        for k, v in obj.items():
            found.extend(_find_scroll_dirs(v, f"{path}/{k}" if path else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(_find_scroll_dirs(v, f"{path}[{i}]"))
    return found


# ---------------------------------------------------------------------------
# Finder (Explorer-like behavior; the F2/Del/cut-paste keys live in Karabiner)
# ---------------------------------------------------------------------------

class Finder(Component):
    name = "finder"
    description = "Finder behaves like Explorer: extensions, path bar, folders first, list view"

    specs = [
        DefaultsSpec("NSGlobalDomain", {"AppleShowAllExtensions": True}),
        DefaultsSpec("com.apple.finder", {
            "ShowPathbar": True,               # path bar ~ Explorer address bar
            "ShowStatusBar": True,
            "_FXSortFoldersFirst": True,       # folders before files, like Windows
            "FXDefaultSearchScope": "SCcf",    # search the current folder
            "FXEnableExtensionChangeWarning": False,
            "NewWindowTarget": "PfHm",         # new windows open home
            "FXPreferredViewStyle": "Nlsv",    # list view ~ Explorer details view
        }),
    ]

    def checks(self):
        return [c for spec in self.specs for c in spec.checks()]

    def apply(self):
        actions = []
        for spec in self.specs:
            actions.extend(spec.apply())
        if actions:
            util.kill_app("Finder")  # Finder relaunches itself
            actions.append("restarted Finder")
        return actions


# ---------------------------------------------------------------------------
# DockDoor (Windows-style Dock: click active app's icon to minimize/restore,
# hover previews). Its Alt+Tab switcher is disabled — AltTab owns that.
# ---------------------------------------------------------------------------

class DockDoor(Component):
    name = "dockdoor"
    description = "DockDoor: click Dock icon to minimize/restore (Windows taskbar), hover previews"
    manual = ["Grant Accessibility and Screen Recording to DockDoor"]

    DOMAIN = "com.ethanbills.DockDoor"
    spec = DefaultsSpec(DOMAIN, {
        "shouldHideOnDockItemClick": True,   # click frontmost app's icon -> minimize
        "dockClickAction": "minimize",       # minimize (click again restores), not hide
        "enableWindowSwitcher": False,       # AltTab owns Alt+Tab
        "showMenuBarIcon": False,
        "openDelay": 0.1,                    # snappier hover previews
        "fadeOutDuration": 0.05,             # previews vanish with the dock…
        "inactivityTimeout": 0.1,            # …and don't linger after mouse leaves
    })

    def checks(self):
        out = self.spec.checks()
        running = util.process_running("DockDoor")
        out.append(Check("DockDoor running", running, "running",
                         "running" if running else "not running"))
        return out

    def apply(self):
        actions = self.spec.apply()
        if actions:
            _restart("DockDoor")
            actions.append("restarted DockDoor")
        elif not util.process_running("DockDoor"):
            util.open_app("DockDoor")
            actions.append("started DockDoor")
        return actions


# ---------------------------------------------------------------------------
# Swift Quit (red X quits the app)
# ---------------------------------------------------------------------------

class SwiftQuit(Component):
    name = "swiftquit"
    description = "Swift Quit: closing an app's last window quits the app"
    manual = ["Grant Accessibility to Swift Quit"]

    DOMAIN = "onebadidea.Swift-Quit"
    spec = DefaultsSpec(DOMAIN, {
        "SwiftQuitSettings": {
            "excludeBehaviour": "excludeApps",  # quit everything not excluded
            "launchAtLogin": True,
            "menubarIconEnabled": True,
        },
    })

    def checks(self):
        out = self.spec.checks()
        running = util.process_running("Swift Quit")
        out.append(Check("Swift Quit running", running, "running",
                         "running" if running else "not running"))
        return out

    def apply(self):
        actions = self.spec.apply()
        if actions:
            _restart("Swift Quit")
            actions.append("restarted Swift Quit")
        elif not util.process_running("Swift Quit"):
            util.open_app("Swift Quit")
            actions.append("started Swift Quit")
        return actions


# ---------------------------------------------------------------------------
# Login items
# ---------------------------------------------------------------------------

class LoginItems(Component):
    name = "login"
    description = "Auto-start the setup's apps at login"

    # AltTab is intentionally absent: it registers launch-at-login itself via
    # SMAppService and deletes any legacy login item on startup (which used to
    # look like mysterious drift). Its component checks that it's running.
    APPS = ["Karabiner-Elements", "Rectangle", "Maccy",
            "UnnaturalScrollWheels", "Swift Quit", "Ghostty", "DockDoor"]

    def checks(self):
        current = util.login_items()
        if current is None:
            return [Check("login items readable", False, "System Events access",
                          "osascript failed",
                          note="grant Automation permission for System Events")]
        missing = [a for a in self.APPS if a not in current]
        return [Check("login items", not missing, ", ".join(self.APPS),
                      "all present" if not missing else "missing: " + ", ".join(missing))]

    def apply(self):
        current = util.login_items()
        if current is None:
            return ["SKIPPED: cannot read login items (System Events access)"]
        actions = []
        for app in self.APPS:
            if app not in current:
                if util.add_login_item(app):
                    actions.append(f"added login item: {app}")
                else:
                    actions.append(f"FAILED to add login item: {app} (app installed?)")
        return actions

    def warnings(self):
        out = []
        p = util.run(["osascript", "-e",
                      'tell application "System Events" to get {name, path} '
                      'of every login item'])
        if p.returncode != 0:
            return out
        parts = [s.strip() for s in p.stdout.strip().split(",")]
        names, paths = parts[:len(parts) // 2], parts[len(parts) // 2:]
        for name, path in zip(names, paths):
            # System Events reports "missing value" when the app is gone.
            if path == "missing value" or (path and not Path(path).exists()):
                out.append(Warning_(
                    f"stale login item: {name}",
                    "its application no longer exists",
                    fix="remove it in System Settings → General → Login Items"))
        return out
