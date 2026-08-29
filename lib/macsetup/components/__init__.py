"""Registry of all managed components (order = display/apply order)."""

from .brew import Brew
from .system import SystemDefaults, SymbolicHotkeys, ZshrcBlock
from .karabiner import Karabiner
from .files import CocoaKeybindings, Ghostty, Scripts, Tmux
from .apps import AltTab, Finder, LoginItems, Maccy, Rectangle, ScrollWheels, SwiftQuit

ALL = [
    Brew(),
    SystemDefaults(),
    SymbolicHotkeys(),
    Karabiner(),
    CocoaKeybindings(),
    Ghostty(),
    Scripts(),
    Tmux(),
    ZshrcBlock(),
    AltTab(),
    Maccy(),
    Rectangle(),
    ScrollWheels(),
    Finder(),
    SwiftQuit(),
    LoginItems(),
]
