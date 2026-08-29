"""Karabiner-Elements: render config template + per-device mappings, install, verify."""

import json
from pathlib import Path

from ..framework import Check, Component, Warning_
from .. import util

TEMPLATE = util.CONFIG / "karabiner" / "karabiner.json"
DEST = util.HOME / ".config" / "karabiner" / "karabiner.json"

# Vendors whose external keyboards have a Mac layout (Cmd next to Space);
# the Windows-layout modifier swap must NOT be applied to them.
APPLE_VENDOR_IDS = {76, 1452}

# Modifier swap for external Windows-layout keyboards
# (physical Ctrl|Win|Alt -> Command|Option|Control).
EXTERNAL_SIMPLE_MODS = [
    {"from": {"key_code": "left_control"}, "to": [{"key_code": "left_command"}]},
    {"from": {"key_code": "left_command"}, "to": [{"key_code": "left_option"}]},
    {"from": {"key_code": "left_option"}, "to": [{"key_code": "left_control"}]},
    {"from": {"key_code": "right_control"}, "to": [{"key_code": "right_command"}]},
    {"from": {"key_code": "right_command"}, "to": [{"key_code": "right_option"}]},
    {"from": {"key_code": "right_option"}, "to": [{"key_code": "right_control"}]},
]


def connected_external_keyboards():
    """External, physical, non-Apple keyboards Karabiner currently sees."""
    p = util.run([util.KARABINER_CLI, "--list-connected-devices"])
    if p.returncode != 0:
        return []
    try:
        devices = json.loads(p.stdout)
    except json.JSONDecodeError:
        return []
    out = []
    for d in devices:
        ident = d.get("device_identifiers", {})
        if not ident.get("is_keyboard"):
            continue
        if d.get("is_built_in_keyboard") or d.get("is_built_in_touch_bar"):
            continue
        if ident.get("is_virtual_device"):
            continue
        vid, pid = ident.get("vendor_id"), ident.get("product_id")
        if vid is None or pid is None or vid in APPLE_VENDOR_IDS:
            continue
        out.append({"vendor_id": vid, "product_id": pid})
    # unique by (vid, pid)
    seen, uniq = set(), []
    for d in out:
        key = (d["vendor_id"], d["product_id"])
        if key not in seen:
            seen.add(key)
            uniq.append(d)
    return uniq


def _device_entry(vid, pid):
    return {
        "identifiers": {"is_keyboard": True, "vendor_id": vid, "product_id": pid},
        "simple_modifications": EXTERNAL_SIMPLE_MODS,
    }


def _is_generated_entry(dev):
    ident = dev.get("identifiers", {})
    return "vendor_id" in ident and not ident.get("is_built_in_keyboard")


def render():
    """Template + generated device entries for currently-connected keyboards."""
    config = json.loads(TEMPLATE.read_text())
    devices = config["profiles"][0].setdefault("devices", [])
    for kb in connected_external_keyboards():
        devices.append(_device_entry(kb["vendor_id"], kb["product_id"]))
    return config


class Karabiner(Component):
    name = "karabiner"
    description = "Key remapping rules and per-keyboard modifier swaps"
    manual = [
        "Grant Accessibility to karabiner_grabber (System Settings → Privacy & Security → Accessibility)",
        "Grant Input Monitoring to karabiner_grabber and karabiner_observer",
    ]

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

        # 2) Every connected external keyboard must have a device entry.
        connected = connected_external_keyboards()
        covered = {(d["identifiers"].get("vendor_id"), d["identifiers"].get("product_id"))
                   for d in live_generated}
        missing = [kb for kb in connected
                   if (kb["vendor_id"], kb["product_id"]) not in covered]
        out.append(Check("connected external keyboards mapped", not missing,
                         f"{len(connected)} keyboard(s) covered",
                         "all covered" if not missing else
                         "unmapped: " + ", ".join(f"vid={k['vendor_id']} pid={k['product_id']}"
                                                  for k in missing)))

        # 3) Generated entries use the current modifier swap.
        stale = [d for d in live_generated
                 if util.norm(d.get("simple_modifications")) != util.norm(EXTERNAL_SIMPLE_MODS)]
        out.append(Check("external keyboard modifier swap current", not stale,
                         "standard Windows-layout swap",
                         "current" if not stale else f"{len(stale)} stale entrie(s)"))
        return out

    def apply(self):
        desired = render()
        # Keep device entries for keyboards that aren't currently connected
        # (e.g. an external keyboard at another desk).
        if DEST.exists():
            try:
                live = json.loads(DEST.read_text())
                have = {(d["identifiers"].get("vendor_id"), d["identifiers"].get("product_id"))
                        for d in desired["profiles"][0]["devices"] if _is_generated_entry(d)}
                for d in live["profiles"][0].get("devices", []):
                    if _is_generated_entry(d):
                        key = (d["identifiers"].get("vendor_id"),
                               d["identifiers"].get("product_id"))
                        if key not in have:
                            desired["profiles"][0]["devices"].append(
                                _device_entry(*key))
            except (json.JSONDecodeError, KeyError):
                pass
        text = json.dumps(desired, indent=4) + "\n"
        if DEST.exists() and DEST.read_text() == text:
            return []
        DEST.parent.mkdir(parents=True, exist_ok=True)
        if DEST.exists():
            import shutil
            shutil.copy2(DEST, util.backup_path(DEST))
        DEST.write_text(text)
        return ["installed karabiner.json (Karabiner reloads automatically)"]

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
        return out
