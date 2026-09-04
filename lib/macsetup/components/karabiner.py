"""Karabiner-Elements: render config template + per-device overrides, install, verify.

Modifier-swap design (any keyboard works without per-device setup):

- The PROFILE-level simple_modifications hold the Windows-layout swap
  (physical Ctrl|Win|Alt -> Command|Option|Control). Karabiner compiles
  device-scoped simple modifications BEFORE profile-level ones and matching is
  first-match, so profile-level entries act as a fallback for any keyboard
  without its own entry — i.e. every external Windows-layout keyboard, current
  or future, is covered with zero configuration.
- The BUILT-IN keyboard has a device-scoped override in the template (Mac
  layout: Ctrl<->Cmd swap, Option kept as itself via an identity mapping so
  the profile fallback can't touch it, plus the paragraph-sign key).
- Apple-vendor EXTERNAL keyboards also have a Mac layout, so `apply` generates
  the same Mac-layout override for any that are connected.
"""

import json
import os
import plistlib
import re

from ..framework import Check, Component, Warning_
from .. import util

TEMPLATE = util.CONFIG / "karabiner" / "karabiner.json"
DEST = util.HOME / ".config" / "karabiner" / "karabiner.json"

# Vendors whose keyboards have a Mac layout (Cmd next to Space).
APPLE_VENDOR_IDS = {76, 1452}

# Override for Apple-layout external keyboards: same net behavior as the
# built-in keyboard (identity mappings block the profile-level fallback).
MAC_LAYOUT_MODS = [
    # fn is the leftmost key on Apple layouts; make it a second Ctrl like the
    # bottom-left key on a Windows keyboard.
    {"from": {"key_code": "fn"}, "to": [{"key_code": "left_command"}]},
    {"from": {"key_code": "left_control"}, "to": [{"key_code": "left_command"}]},
    {"from": {"key_code": "left_command"}, "to": [{"key_code": "left_control"}]},
    {"from": {"key_code": "left_option"}, "to": [{"key_code": "left_option"}]},
    {"from": {"key_code": "right_control"}, "to": [{"key_code": "right_command"}]},
    {"from": {"key_code": "right_command"}, "to": [{"key_code": "right_control"}]},
    {"from": {"key_code": "right_option"}, "to": [{"key_code": "right_option"}]},
]


def connected_apple_external_keyboards():
    """Connected physical Apple-vendor keyboards that aren't the built-in one."""
    p = util.run([util.KARABINER_CLI, "--list-connected-devices"])
    if p.returncode != 0:
        return []
    try:
        devices = json.loads(p.stdout)
    except json.JSONDecodeError:
        return []
    out, seen = [], set()
    for d in devices:
        ident = d.get("device_identifiers", {})
        if not ident.get("is_keyboard"):
            continue
        if d.get("is_built_in_keyboard") or d.get("is_built_in_touch_bar"):
            continue
        if ident.get("is_virtual_device"):
            continue
        vid, pid = ident.get("vendor_id"), ident.get("product_id")
        if vid not in APPLE_VENDOR_IDS or pid is None:
            continue
        if (vid, pid) not in seen:
            seen.add((vid, pid))
            out.append({"vendor_id": vid, "product_id": pid})
    return out


def _device_entry(vid, pid):
    return {
        "identifiers": {"is_keyboard": True, "vendor_id": vid, "product_id": pid},
        "simple_modifications": MAC_LAYOUT_MODS,
    }


def _is_generated_entry(dev):
    ident = dev.get("identifiers", {})
    return "vendor_id" in ident and not ident.get("is_built_in_keyboard")


def render():
    """Template + Mac-layout overrides for connected Apple external keyboards."""
    config = json.loads(TEMPLATE.read_text())
    devices = config["profiles"][0].setdefault("devices", [])
    for kb in connected_apple_external_keyboards():
        devices.append(_device_entry(kb["vendor_id"], kb["product_id"]))
    return config


WAKE_LABEL = "com.macsetup.karabiner-wake"
WAKE_PLIST = util.HOME / "Library" / "LaunchAgents" / f"{WAKE_LABEL}.plist"
WAKE_SCRIPT = util.HOME / ".local" / "bin" / "macsetup-karabiner-wake"


def _wake_agent_plist():
    """LaunchAgent that repairs Karabiner after sleep/wake.

    StartInterval (not a wake trigger, which launchd lacks): the timer expires
    while the Mac sleeps, so launchd runs the job right after wake. The script
    itself acts only once per wake.
    """
    return {
        "Label": WAKE_LABEL,
        "ProgramArguments": [str(WAKE_SCRIPT)],
        "StartInterval": 60,
        "RunAtLoad": True,
        "ProcessType": "Background",
        "LowPriorityIO": True,
    }


class Karabiner(Component):
    name = "karabiner"
    description = "Key remapping: profile-wide Windows swap (any keyboard), wake self-repair"
    manual = [
        "Grant Accessibility to karabiner_grabber (System Settings → Privacy & Security → Accessibility)",
        "Grant Input Monitoring to karabiner_grabber and karabiner_observer",
    ]

    def _agent_loaded(self):
        return util.run_ok(["launchctl", "print",
                            f"gui/{os.getuid()}/{WAKE_LABEL}"])

    def _agent_checks(self):
        want = _wake_agent_plist()
        try:
            have = plistlib.loads(WAKE_PLIST.read_bytes())
        except (OSError, plistlib.InvalidFileException):
            have = None
        installed = have == want
        loaded = self._agent_loaded()
        return [
            Check("wake self-repair agent installed", installed,
                  f"{WAKE_PLIST.name} matching spec",
                  "installed" if installed else
                  ("missing" if have is None else "outdated")),
            Check("wake self-repair agent loaded", loaded, "loaded in launchd",
                  "loaded" if loaded else "not loaded"),
        ]

    @staticmethod
    def _seed_wake_state():
        """Mark the current wake as handled.

        The agent runs at load; without this, installing it would restart
        Karabiner immediately — an unwanted side effect of `apply`, and a
        restart mid-keypress can strand a key down.
        """
        state = (util.HOME / ".local" / "state" / "macsetup" / "karabiner-wake")
        if state.exists():
            return
        p = util.run(["sysctl", "-n", "kern.waketime"])
        m = re.search(r"(\d+)", p.stdout or "")
        if m:
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(m.group(1) + "\n")

    def _apply_agent(self):
        actions = []
        self._seed_wake_state()
        want = _wake_agent_plist()
        try:
            have = plistlib.loads(WAKE_PLIST.read_bytes())
        except (OSError, plistlib.InvalidFileException):
            have = None
        if have != want:
            WAKE_PLIST.parent.mkdir(parents=True, exist_ok=True)
            WAKE_PLIST.write_bytes(plistlib.dumps(want))
            actions.append(f"installed {WAKE_PLIST.name}")
        if actions or not self._agent_loaded():
            domain = f"gui/{os.getuid()}"
            util.run(["launchctl", "bootout", f"{domain}/{WAKE_LABEL}"])
            if util.run_ok(["launchctl", "bootstrap", domain, str(WAKE_PLIST)]):
                actions.append("loaded wake self-repair agent")
            else:
                actions.append("FAILED to load wake self-repair agent")
        return actions

    def checks(self):
        out = []
        if not DEST.exists():
            return [Check("~/.config/karabiner/karabiner.json", False,
                          "installed", "missing")]
        try:
            live = json.loads(DEST.read_text())
        except json.JSONDecodeError:
            return [Check("karabiner.json valid JSON", False, "parseable", "corrupt")]

        template = json.loads(TEMPLATE.read_text())

        # 1) Everything except generated device entries must match the template.
        live_cmp = json.loads(json.dumps(live))
        live_generated = [d for d in live_cmp["profiles"][0].get("devices", [])
                          if _is_generated_entry(d)]
        live_cmp["profiles"][0]["devices"] = [
            d for d in live_cmp["profiles"][0].get("devices", [])
            if not _is_generated_entry(d)]
        ok = util.norm(live_cmp) == util.norm(template)
        out.append(Check("rules/settings match repo template", ok,
                         "template + generated devices", "match" if ok else "differ",
                         note="" if ok else "run `macsetup apply karabiner` "
                              "(or `adopt` if the live edit is intentional)"))

        # 2) Connected Apple external keyboards need a Mac-layout override,
        #    or the profile-level Windows swap would wrongly apply to them.
        connected = connected_apple_external_keyboards()
        covered = {(d["identifiers"].get("vendor_id"), d["identifiers"].get("product_id"))
                   for d in live_generated
                   if util.norm(d.get("simple_modifications")) == util.norm(MAC_LAYOUT_MODS)}
        missing = [kb for kb in connected
                   if (kb["vendor_id"], kb["product_id"]) not in covered]
        out.append(Check("Apple external keyboards have Mac-layout overrides", not missing,
                         f"{len(connected)} Apple external keyboard(s) covered",
                         "all covered" if not missing else
                         "unmapped: " + ", ".join(f"vid={k['vendor_id']} pid={k['product_id']}"
                                                  for k in missing)))
        out.extend(self._agent_checks())
        return out

    def apply(self):
        desired = render()
        # Keep Mac-layout overrides for Apple keyboards that aren't currently
        # connected (e.g. one at another desk).
        if DEST.exists():
            try:
                live = json.loads(DEST.read_text())
                have = {(d["identifiers"].get("vendor_id"), d["identifiers"].get("product_id"))
                        for d in desired["profiles"][0]["devices"] if _is_generated_entry(d)}
                for d in live["profiles"][0].get("devices", []):
                    # Only carry over entries this tool generated (a Mac-layout
                    # override for an Apple keyboard). Anything else in the live
                    # file is a manual edit and must not be resurrected.
                    if (_is_generated_entry(d)
                            and util.norm(d.get("simple_modifications"))
                            == util.norm(MAC_LAYOUT_MODS)):
                        ident = d["identifiers"]
                        key = (ident.get("vendor_id"), ident.get("product_id"))
                        if key not in have and key[0] in APPLE_VENDOR_IDS:
                            desired["profiles"][0]["devices"].append(
                                _device_entry(*key))
            except (json.JSONDecodeError, KeyError):
                pass
        actions = []
        text = json.dumps(desired, indent=4) + "\n"
        if not DEST.exists() or DEST.read_text() != text:
            DEST.parent.mkdir(parents=True, exist_ok=True)
            if DEST.exists():
                import shutil
                shutil.copy2(DEST, util.backup_path(DEST))
            DEST.write_text(text)
            actions.append("installed karabiner.json (Karabiner reloads automatically)")
        actions.extend(self._apply_agent())
        return actions

    def warnings(self):
        out = []
        # Karabiner 15.x process names (the pre-15 karabiner_grabber is gone).
        for proc, why in [
            ("Karabiner-Core-Service", "key remapping is NOT active"),
            ("Karabiner-VirtualHIDDevice-Daemon", "virtual keyboard device not running"),
            ("karabiner_console_user_server", "Karabiner user session agent not running"),
        ]:
            if not util.process_running(proc):
                out.append(Warning_(
                    f"{proc} not running", why,
                    fix="open Karabiner-Elements and grant its permissions"))
        # After sleep/wake Karabiner tears down and recreates its virtual
        # keyboard; if the last recorded state is not-ready, remapping is dead
        # or dying (all shortcuts revert to raw keys) until it recovers.
        try:
            lines = [l for l in
                     open("/var/log/karabiner/core_service.log", errors="ignore")
                     if "virtual_hid_keyboard_ready_response" in l]
            if lines and lines[-1].rstrip().endswith("false"):
                out.append(Warning_(
                    "Karabiner virtual keyboard not ready",
                    "the last logged state is not-ready (often after sleep/wake); "
                    "remapping may be inactive",
                    fix="wait a few seconds; if it persists, quit and reopen "
                        "Karabiner-Elements"))
        except OSError:
            pass
        return out
