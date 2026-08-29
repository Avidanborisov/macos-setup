"""Config files copied from the repo into place (with adopt for reverse sync)."""

from ..framework import FileComponent
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
    description = "Helper scripts in ~/.local/bin (tmux launcher, Win+Down helper)"
    pairs = [
        (util.CONFIG / "bin" / "ghostty-tmux-launch",
         util.HOME / ".local" / "bin" / "ghostty-tmux-launch", 0o755),
        (util.CONFIG / "bin" / "macsetup-win-down",
         util.HOME / ".local" / "bin" / "macsetup-win-down", 0o755),
    ]



class Tmux(FileComponent):
    name = "tmux"
    description = "tmux configuration (oh-my-tmux + local overrides, prefix = C-a)"
    pairs = [
        (util.CONFIG / "tmux" / "tmux.conf", util.HOME / ".tmux.conf", None),
        (util.CONFIG / "tmux" / "tmux.conf.local", util.HOME / ".tmux.conf.local", None),
    ]
    restart_note = "note: reload with `tmux source ~/.tmux.conf` in a running session"

