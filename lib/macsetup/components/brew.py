"""Homebrew apps and CLI tools."""

import shutil
from pathlib import Path

from ..framework import Check, Component, Warning_
from .. import util

# GUI apps required by the Windows-behavior setup
CASKS_CORE = [
    "karabiner-elements",   # key remapping
    "rectangle",            # window snapping (Win+Arrows)
    "alt-tab",              # Windows-style Alt+Tab
    "maccy",                # clipboard history (Win+V)
    "ghostty",              # terminal
    "unnaturalscrollwheels",  # reverse mouse wheel only (trackpad stays natural)
    "dockdoor",             # Windows-style Dock: click-to-minimize, hover previews
]

# CLI tools I like having everywhere
FORMULAE = [
    "asitop", "btop", "cmake", "ddgr", "dockutil", "fd", "fzf", "gh",
    "git-lfs", "gnuplot", "graphviz", "htop", "hyperfine", "ipython", "jq",
    "ncdu", "ninja", "node", "nvtop", "ollama", "pandoc", "pdfgrep",
    "ripgrep", "screenfetch", "the_silver_searcher", "tmux", "watch", "wget",
]

# Installed apps that duplicate/conflict with the managed setup
CONFLICTS = {
    "scroll-reverser": "duplicates UnnaturalScrollWheels (scroll inversion)",
    "redquits": "duplicates DockDoor's quit-on-last-window-close (red X quits the app)",
}

BREW_PREFIX = Path("/opt/homebrew")


def _installed_casks():
    return {p.name for p in (BREW_PREFIX / "Caskroom").iterdir()} \
        if (BREW_PREFIX / "Caskroom").exists() else set()


def _installed_formulae():
    return {p.name for p in (BREW_PREFIX / "opt").iterdir()} \
        if (BREW_PREFIX / "opt").exists() else set()


class Brew(Component):
    name = "brew"
    description = "Homebrew casks (GUI apps) and formulae (CLI tools)"

    def checks(self):
        out = []
        if not shutil.which("brew"):
            return [Check("homebrew installed", False, "brew on PATH", "not found",
                          note="install from https://brew.sh")]
        casks = _installed_casks()
        formulae = _installed_formulae()
        missing_casks = [c for c in CASKS_CORE if c not in casks]
        missing_formulae = [f for f in FORMULAE if f not in formulae]
        out.append(Check("casks installed", not missing_casks,
                         ", ".join(CASKS_CORE),
                         "all present" if not missing_casks
                         else "missing: " + ", ".join(missing_casks)))
        out.append(Check("formulae installed", not missing_formulae,
                         f"{len(FORMULAE)} tools",
                         "all present" if not missing_formulae
                         else "missing: " + ", ".join(missing_formulae)))
        return out

    def apply(self):
        actions = []
        if not shutil.which("brew"):
            return ["SKIPPED: Homebrew not installed (https://brew.sh)"]
        casks = _installed_casks()
        formulae = _installed_formulae()
        missing_casks = [c for c in CASKS_CORE if c not in casks]
        missing_formulae = [f for f in FORMULAE if f not in formulae]
        if missing_casks:
            util.run(["brew", "install", "--cask"] + missing_casks, timeout=1800)
            actions.append("brew install --cask " + " ".join(missing_casks))
        if missing_formulae:
            util.run(["brew", "install"] + missing_formulae, timeout=1800)
            actions.append("brew install " + " ".join(missing_formulae))
        return actions

    def warnings(self):
        out = []
        casks = _installed_casks()
        for cask, why in CONFLICTS.items():
            if cask in casks:
                out.append(Warning_(
                    f"conflicting app installed: {cask}", why,
                    fix=f"brew uninstall --cask {cask}"))
        return out
