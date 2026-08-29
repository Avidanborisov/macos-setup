"""Shared helpers: subprocess, defaults/plist access, paths, terminal colors."""

import datetime
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CONFIG = REPO / "config"
HOME = Path.home()

KARABINER_CLI = "/Library/Application Support/org.pqrs/Karabiner-Elements/bin/karabiner_cli"


def run(cmd, check=False, capture=True, timeout=120):
    """Run a command (list of args). Returns CompletedProcess with text output."""
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=True,
        timeout=timeout,
    )


def run_ok(cmd, timeout=120):
    """Run a command, return True if it exited 0."""
    try:
        return run(cmd, timeout=timeout).returncode == 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# defaults / plist access
# ---------------------------------------------------------------------------

def defaults_export(domain):
    """Read an entire defaults domain as a Python dict (empty if missing)."""
    p = run(["defaults", "export", domain, "-"])
    if p.returncode != 0 or not p.stdout:
        return {}
    try:
        return plistlib.loads(p.stdout.encode())
    except Exception:
        # Fall back to binary read via a temp path
        return {}


def defaults_write(domain, key, value):
    """Write a single defaults key with the right type flag."""
    if isinstance(value, bool):
        args = ["-bool", "true" if value else "false"]
    elif isinstance(value, int):
        args = ["-int", str(value)]
    elif isinstance(value, float):
        args = ["-float", str(value)]
    elif isinstance(value, str):
        args = ["-string", value]
    elif isinstance(value, dict):
        # Serialize as an XML plist fragment; `defaults write` accepts it.
        xml = plistlib.dumps(value).decode()
        # strip header/footer, keep the <dict>...</dict> body
        body = xml[xml.index("<dict>"): xml.rindex("</dict>") + len("</dict>")]
        args = [body]
    elif isinstance(value, list):
        xml = plistlib.dumps(value).decode()
        body = xml[xml.index("<array>"): xml.rindex("</array>") + len("</array>")]
        args = [body]
    else:
        raise TypeError(f"unsupported defaults type: {type(value)}")
    run(["defaults", "write", domain, key] + args, check=True)


def norm(value):
    """Normalize plist values for comparison.

    Bools/ints/floats collapse to ints where equal, and numeric or boolean
    *strings* collapse too — some apps (AltTab) persist their prefs as
    strings like "true"/"0" which would otherwise read as permanent drift.
    """
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        # float32 storage (Rectangle) turns 0.3 into 0.30000001192…
        value = round(value, 5)
        return int(value) if value == int(value) else value
    if isinstance(value, str):
        low = value.strip().lower()
        if low in ("true", "yes"):
            return 1
        if low in ("false", "no"):
            return 0
        try:
            return int(low)
        except ValueError:
            pass
    if isinstance(value, dict):
        return {k: norm(v) for k, v in value.items()}
    if isinstance(value, list):
        return [norm(v) for v in value]
    return value


# ---------------------------------------------------------------------------
# files
# ---------------------------------------------------------------------------

def backup_path(dest: Path) -> Path:
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return dest.with_name(dest.name + f".backup.{stamp}")


def install_file(src: Path, dest: Path, mode=None) -> bool:
    """Copy src to dest (backing up an existing, different dest). Returns True if changed."""
    return install_bytes(src.read_bytes(), dest, mode)


def install_bytes(content: bytes, dest: Path, mode=None) -> bool:
    """Write content to dest (backing up an existing, different dest). Returns True if changed."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if dest.read_bytes() == content:
            if mode is not None:
                os.chmod(dest, mode)
            return False
        shutil.copy2(dest, backup_path(dest))
    dest.write_bytes(content)
    if mode is not None:
        os.chmod(dest, mode)
    return True


def files_match(a: Path, b: Path) -> bool:
    return a.exists() and b.exists() and a.read_bytes() == b.read_bytes()


# ---------------------------------------------------------------------------
# apps / processes
# ---------------------------------------------------------------------------

def app_path(app_name):
    for base in ("/Applications", "/Applications/Utilities", str(HOME / "Applications")):
        p = Path(base) / f"{app_name}.app"
        if p.exists():
            return p
    return None


def process_running(name):
    return run_ok(["pgrep", "-x", name])


def kill_app(name):
    run(["killall", name])


def open_app(name):
    return run_ok(["open", "-a", name])


def login_items():
    p = run(["osascript", "-e",
             'tell application "System Events" to get name of every login item'])
    if p.returncode != 0:
        return None
    out = p.stdout.strip()
    return [s.strip() for s in out.split(",")] if out else []


def add_login_item(app_name):
    path = app_path(app_name)
    if not path:
        return False
    return run_ok([
        "osascript", "-e",
        f'tell application "System Events" to make login item at end '
        f'with properties {{path:"{path}", hidden:false, name:"{app_name}"}}',
    ])


# ---------------------------------------------------------------------------
# terminal output
# ---------------------------------------------------------------------------

_TTY = sys.stdout.isatty()


def _c(code, s):
    return f"\033[{code}m{s}\033[0m" if _TTY else s


def green(s):
    return _c("32", s)


def red(s):
    return _c("31", s)


def yellow(s):
    return _c("33", s)


def bold(s):
    return _c("1", s)


def dim(s):
    return _c("2", s)
