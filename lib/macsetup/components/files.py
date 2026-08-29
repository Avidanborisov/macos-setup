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
    description = "Ghostty terminal config, icon, and tmux launcher script"
    pairs = [
        (util.CONFIG / "ghostty" / "config",
         util.HOME / ".config" / "ghostty" / "config", None),
        (util.CONFIG / "ghostty" / "icon_256x256@2x.png",
         util.HOME / ".config" / "ghostty" / "icon_256x256@2x.png", None),
        (util.CONFIG / "bin" / "ghostty-tmux-launch",
         util.HOME / ".local" / "bin" / "ghostty-tmux-launch", 0o755),
    ]
    restart_note = "note: restart Ghostty to pick up config changes"



class Tmux(FileComponent):
    name = "tmux"
    description = "tmux configuration (oh-my-tmux + local overrides, prefix = C-a)"
    pairs = [
        (util.CONFIG / "tmux" / "tmux.conf", util.HOME / ".tmux.conf", None),
        (util.CONFIG / "tmux" / "tmux.conf.local", util.HOME / ".tmux.conf.local", None),
    ]
    restart_note = "note: reload with `tmux source ~/.tmux.conf` in a running session"

