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
    # AltTab's ShowHowPreference enum — NOT a boolean, and easy to get
    # backwards: 0 = show, 1 = hide, 2 = show at the end. Keys without a
    # numeric suffix belong to shortcut index 0, which is our hold shortcut.
    SHOW, HIDE, SHOW_AT_END = 0, 1, 2
    spec = DefaultsSpec(DOMAIN, {
        # Windows' Alt+Tab lists everything stashed — dock clicks minimize and
        # Cmd+H hides — so both must stay reachable here.
        "showMinimizedWindows": SHOW,
        "showHiddenWindows": SHOW,
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
    # Settings are kept as a JSON snapshot so they can be tuned in DockDoor's
    # own UI and pulled back with `macsetup adopt dockdoor`.
    SETTINGS = util.CONFIG / "dockdoor" / "settings.json"
    # Runtime state, not preferences — never tracked.
    VOLATILE_PREFIXES = ("SU", "NSWindow Frame", "NSStatusItem")
    VOLATILE = {"launched", "lastKnownScreenRecordingPermission",
                "persistedWindowOrder", "reopenSettingsAfterRestart", "migrations"}

    def _desired(self):
        return json.loads(self.SETTINGS.read_text())

    def _tracked_live(self):
        live = util.defaults_export(self.DOMAIN)
        return {k: v for k, v in live.items()
                if k not in self.VOLATILE
                and not k.startswith(self.VOLATILE_PREFIXES)}

    def checks(self):
        live = util.defaults_export(self.DOMAIN)
        desired = self._desired()
        bad = [k for k, v in desired.items()
               if util.norm(live.get(k)) != util.norm(v)]
        out = [Check("DockDoor settings", not bad,
                     f"{len(desired)} keys from config/dockdoor/settings.json",
                     "all match" if not bad else "drifted: " + ", ".join(sorted(bad)[:6])
                     + ("…" if len(bad) > 6 else ""))]
        running = util.process_running("DockDoor")
        out.append(Check("DockDoor running", running, "running",
                         "running" if running else "not running"))
        return out

    def apply(self):
        live = util.defaults_export(self.DOMAIN)
        actions = []
        for key, value in self._desired().items():
            if util.norm(live.get(key)) != util.norm(value):
                util.defaults_write(self.DOMAIN, key, value)
                actions.append(f"set DockDoor {key}")
        if actions:
            _restart("DockDoor")
            actions.append("restarted DockDoor")
        elif not util.process_running("DockDoor"):
            util.open_app("DockDoor")
            actions.append("started DockDoor")
        return actions

    def adoptable(self):
        return True

    def adopt(self):
        live = self._tracked_live()
        if util.norm(live) == util.norm(self._desired()):
            return []

        def clean(v):
            if isinstance(v, float):
                return round(v, 5)   # float32 storage noise
            if isinstance(v, list):
                return [clean(x) for x in v]
            return v

        snapshot = {k: clean(v) for k, v in sorted(live.items())}
        self.SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        self.SETTINGS.write_text(json.dumps(snapshot, indent=2) + "\n")
        return [f"adopted live DockDoor settings -> "
                f"{self.SETTINGS.relative_to(util.REPO)}"]


# ---------------------------------------------------------------------------
# Chrome rtl-toggle extension (Ctrl+Shift RTL/LTR in Chrome text fields)
# ---------------------------------------------------------------------------

class ChromeRtl(Component):
    name = "chrome-rtl"
    description = "Chrome extension: Ctrl+LeftShift/RightShift set LTR/RTL in text fields"
    manual = ["After the first install: restart Chrome and click Enable on its "
              "'new extension added' prompt"]

    SRC = util.CONFIG / "chrome" / "rtl-toggle"
    STORE = util.HOME / "Library" / "Application Support" / "macsetup"
    KEY = STORE / "rtl-toggle.pem"          # machine-local; determines the id
    CRX = STORE / "rtl-toggle.crx"
    EXT_DIR = (util.HOME / "Library" / "Application Support" / "Google" /
               "Chrome" / "External Extensions")
    CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    def _version(self):
        return json.loads((self.SRC / "manifest.json").read_text())["version"]

    def _ext_id(self):
        """Chrome extension id: first 16 bytes of SHA-256 of the DER public
        key, hex nibbles mapped onto a-p."""
        if not self.KEY.exists():
            return None
        import hashlib
        import subprocess
        der = subprocess.run(
            ["openssl", "rsa", "-in", str(self.KEY), "-pubout",
             "-outform", "DER"],
            capture_output=True)  # binary output — must not be text-decoded
        if der.returncode != 0:
            return None
        digest = hashlib.sha256(der.stdout).hexdigest()[:32]
        return "".join(chr(ord("a") + int(c, 16)) for c in digest)

    def _crx_stale(self):
        if not self.CRX.exists():
            return True
        src_mtime = max(p.stat().st_mtime for p in self.SRC.iterdir())
        return self.CRX.stat().st_mtime < src_mtime

    def _json_path(self):
        ext_id = self._ext_id()
        return self.EXT_DIR / f"{ext_id}.json" if ext_id else None

    def _deployed_ok(self):
        jp = self._json_path()
        if not jp or not jp.exists() or self._crx_stale():
            return False
        try:
            data = json.loads(jp.read_text())
        except json.JSONDecodeError:
            return False
        return (data.get("external_crx") == str(self.CRX)
                and data.get("external_version") == self._version())

    def checks(self):
        if not Path(self.CHROME_BIN).exists():
            return [Check("Chrome installed", False, "Google Chrome.app",
                          "not found", note="rtl-toggle needs Chrome")]
        ok = self._deployed_ok()
        return [Check("rtl-toggle registered as Chrome external extension", ok,
                      f"packed v{self._version()} + descriptor in External Extensions",
                      "deployed" if ok else "missing or outdated")]

    def apply(self):
        if not Path(self.CHROME_BIN).exists():
            return ["SKIPPED: Google Chrome not installed"]
        if self._deployed_ok():
            return []
        actions = []
        self.STORE.mkdir(parents=True, exist_ok=True)
        if not self.KEY.exists():
            util.run(["openssl", "genrsa", "-out", str(self.KEY), "2048"],
                     check=True)
            actions.append("generated machine-local extension signing key")
        # Pack from a temp copy: --pack-extension drops the .crx next to the
        # source directory, and the repo should stay free of build artifacts.
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "rtl-toggle"
            shutil.copytree(self.SRC, work)
            util.run([self.CHROME_BIN, f"--pack-extension={work}",
                      f"--pack-extension-key={self.KEY}", "--no-message-box"],
                     check=True)
            packed = work.with_suffix(".crx")
            if not packed.exists():
                return actions + ["FAILED: Chrome --pack-extension produced no crx"]
            shutil.copy2(packed, self.CRX)
        actions.append(f"packed rtl-toggle v{self._version()} -> {self.CRX}")
        self.EXT_DIR.mkdir(parents=True, exist_ok=True)
        self._json_path().write_text(json.dumps({
            "external_crx": str(self.CRX),
            "external_version": self._version(),
        }, indent=2) + "\n")
        actions.append(f"registered external extension ({self._ext_id()})")
        actions.append("note: restart Chrome, then click Enable on its prompt")
        return actions

    def warnings(self):
        ext_id = self._ext_id()
        if not ext_id or not self._deployed_ok():
            return []
        # If Chrome has already ingested it, the id appears in the profile's
        # Secure Preferences; until then a restart (+ Enable click) is pending.
        prefs = (util.HOME / "Library" / "Application Support" / "Google" /
                 "Chrome" / "Default" / "Secure Preferences")
        try:
            if ext_id in prefs.read_text():
                return []
        except OSError:
            return []
        return [Warning_(
            "rtl-toggle not active in Chrome yet",
            "the external-extension descriptor is deployed, but Chrome hasn't "
            "picked it up",
            fix="restart Chrome and click Enable on the 'new extension' prompt")]


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
