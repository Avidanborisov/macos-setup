"""Registry of all managed components (order = display/apply order)."""

from .brew import Brew
from .system import SystemDefaults, SymbolicHotkeys, ZshrcBlock
from .karabiner import Karabiner
from .files import CocoaKeybindings, Ghostty, Tmux
from .apps import AltTab, Maccy, Rectangle, ScrollWheels, LoginItems

ALL = [
    Brew(),
    SystemDefaults(),
    SymbolicHotkeys(),
    Karabiner(),
    CocoaKeybindings(),
    Ghostty(),
    Tmux(),
    ZshrcBlock(),
    AltTab(),
    Maccy(),
    Rectangle(),
    ScrollWheels(),
    LoginItems(),
]
