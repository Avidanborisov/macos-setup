"""Config files copied from the repo into place (with adopt for reverse sync)."""

from ..framework import Check, DefaultsSpec, FileComponent
from .. import util


class CocoaKeybindings(FileComponent):
    name = "keybindings"
    description = "DefaultKeyBinding.dict: Page Up/Down move the cursor (Cocoa apps)"
    pairs = [
        (util.CONFIG / "keybindings" / "DefaultKeyBinding.dict",
         util.HOME / "Library" / "KeyBindings" / "DefaultKeyBinding.dict", None),
    ]
    restart_note = "note: apps pick up DefaultKeyBinding.dict on their next launch"



class Ghostty(FileComponent):
    name = "ghostty"
    description = "Ghostty terminal config and icon"
    pairs = [
        (util.CONFIG / "ghostty" / "config",
         util.HOME / ".config" / "ghostty" / "config", None),
        (util.CONFIG / "ghostty" / "icon_256x256@2x.png",
         util.HOME / ".config" / "ghostty" / "icon_256x256@2x.png", None),
    ]
    template_files = (util.CONFIG / "ghostty" / "config",)
    restart_note = "note: restart Ghostty to pick up config changes"


class Scripts(FileComponent):
    name = "scripts"
    description = "Helper scripts in ~/.local/bin (tmux launcher)"
    pairs = [
        (util.CONFIG / "bin" / "ghostty-tmux-launch",
         util.HOME / ".local" / "bin" / "ghostty-tmux-launch", 0o755),
    ]


class Hammerspoon(FileComponent):
    name = "hammerspoon"
    description = "Hammerspoon: instant Win+Up/Win+Down semantics (maximize/restore/minimize)"
    manual = ["Grant Accessibility to Hammerspoon"]
    pairs = [
        (util.CONFIG / "hammerspoon" / "init.lua",
         util.HOME / ".hammerspoon" / "init.lua", None),
    ]
    spec = DefaultsSpec("org.hammerspoon.Hammerspoon", {
        "MJShowMenuIconKey": False,
        "MJShowDockIconKey": False,
    })

    def checks(self):
        out = super().checks()
        out.extend(self.spec.checks())
        running = util.process_running("Hammerspoon")
        out.append(Check("Hammerspoon running", running, "running",
                         "running" if running else "not running"))
        return out

    def apply(self):
        actions = super().apply()
        actions.extend(self.spec.apply())
        if actions or not util.process_running("Hammerspoon"):
            util.kill_app("Hammerspoon")
            import time
            time.sleep(1)
            util.open_app("Hammerspoon")
            actions.append("restarted Hammerspoon")
        return actions



class Tmux(FileComponent):
    name = "tmux"
    description = "tmux configuration (oh-my-tmux + local overrides, prefix = C-a)"
    pairs = [
        (util.CONFIG / "tmux" / "tmux.conf", util.HOME / ".tmux.conf", None),
        (util.CONFIG / "tmux" / "tmux.conf.local", util.HOME / ".tmux.conf.local", None),
    ]
    restart_note = "note: reload with `tmux source ~/.tmux.conf` in a running session"

