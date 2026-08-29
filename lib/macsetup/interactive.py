"""Interactive verification: real keypresses read in raw mode + GUI yes/no checks.

Terminal key tests are objective — we put the tty in raw mode, ask for one
physical keypress, and assert on the bytes (or signal) that arrive after the
whole Karabiner -> Ghostty -> tmux pipeline. GUI tests can't be observed from
a terminal, so they ask for confirmation.
"""

import os
import select
import signal
import sys
import termios
import tty

from .util import bold, dim, green, red, yellow

ESC = "\x1b"


class KeyTest:
    """Ask for one keypress; pass if the received bytes match any expectation."""

    def __init__(self, name, instruction, expected, note=""):
        self.name = name
        self.instruction = instruction
        self.expected = expected  # list of acceptable byte strings
        self.note = note

    def run(self):
        print(f"  {bold(self.instruction)}", end=" ", flush=True)
        data, got_sigint, got_sigtstp = _read_key()
        if got_sigint and "SIGINT" in self.expected:
            return True, "SIGINT delivered"
        if got_sigtstp and "SIGTSTP" in self.expected:
            return True, "SIGTSTP delivered"
        for exp in self.expected:
            if exp in ("SIGINT", "SIGTSTP"):
                continue
            if data == exp.encode():
                return True, f"got {data!r}"
        if got_sigint or got_sigtstp:
            return False, "got signal " + ("SIGINT" if got_sigint else "SIGTSTP")
        return False, f"got {data!r}, expected one of {self.expected!r}"


class GuiTest:
    """Instruct the user, then ask whether it worked."""

    def __init__(self, name, instruction, question, note=""):
        self.name = name
        self.instruction = instruction
        self.question = question
        self.note = note

    def run(self):
        print(f"  {bold(self.instruction)}")
        while True:
            answer = input(f"  {self.question} [y/n/s(kip)] ").strip().lower()
            if answer in ("y", "yes"):
                return True, "confirmed"
            if answer in ("n", "no"):
                return False, "user reported failure"
            if answer in ("s", "skip"):
                return None, "skipped"


def _read_key(timeout=15.0):
    """Read one keypress (possibly a multi-byte escape sequence) in raw mode."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    flags = {"sigint": False, "sigtstp": False}

    def on_int(_sig, _frm):
        flags["sigint"] = True

    def on_tstp(_sig, _frm):
        flags["sigtstp"] = True

    old_int = signal.signal(signal.SIGINT, on_int)
    old_tstp = signal.signal(signal.SIGTSTP, on_tstp)
    data = b""
    try:
        tty.setraw(fd)  # raw mode still delivers no signals; read bytes instead
        r, _, _ = select.select([fd], [], [], timeout)
        if r:
            data = os.read(fd, 32)
            # collect any trailing bytes of an escape sequence
            while True:
                r, _, _ = select.select([fd], [], [], 0.05)
                if not r:
                    break
                data += os.read(fd, 32)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        signal.signal(signal.SIGINT, old_int)
        signal.signal(signal.SIGTSTP, old_tstp)
    # In raw mode ISIG is off, so Ctrl+C/Ctrl+Z arrive as bytes, not signals.
    if data == b"\x03":
        flags["sigint"] = True
    if data == b"\x1a":
        flags["sigtstp"] = True
    print()
    return data, flags["sigint"], flags["sigtstp"]


def terminal_key_tests():
    """Physical keys whose terminal byte stream we can assert on.

    Expected values cover both direct-to-Ghostty and through-tmux encodings.
    """
    return [
        KeyTest("Home reaches shell",
                "Press the Home key:",
                [f"{ESC}[H", f"{ESC}OH", f"{ESC}[1~"],
                note="single press must arrive — no tmux prefix swallowing"),
        KeyTest("End reaches shell",
                "Press the End key:",
                [f"{ESC}[F", f"{ESC}OF", f"{ESC}[4~"]),
        KeyTest("Ctrl+Left = word left",
                "Hold physical Ctrl and press Left Arrow:",
                [f"{ESC}b"]),
        KeyTest("Ctrl+Right = word right",
                "Hold physical Ctrl and press Right Arrow:",
                [f"{ESC}f"]),
        KeyTest("Ctrl+Backspace deletes word",
                "Hold physical Ctrl and press Backspace:",
                [f"{ESC}\x7f"]),
        KeyTest("Ctrl+C sends interrupt",
                "Hold physical Ctrl and press C:",
                ["SIGINT"]),
        KeyTest("Ctrl+D sends EOF",
                "Hold physical Ctrl and press D:",
                ["\x04"]),
        KeyTest("DEL key forward-deletes",
                "Press the Delete (DEL/forward delete) key:",
                [f"{ESC}[3~"]),
        KeyTest("Page Up passes through",
                "Press Page Up:",
                [f"{ESC}[5~"]),
    ]


def gui_tests():
    return [
        GuiTest("Win+Left snaps window",
                "Focus some window, hold physical Win and press Left Arrow.",
                "Did the window snap to the left half?"),
        GuiTest("Win+Up maximizes",
                "Hold physical Win and press Up Arrow.",
                "Did the window maximize?"),
        GuiTest("Alt+Tab switcher",
                "Hold physical Alt, tap Tab (keep holding Alt).",
                "Did the AltTab window switcher appear?"),
        GuiTest("Alt+Tab arrow navigation",
                "While the switcher is open (Alt held), press the arrow keys, then release Alt.",
                "Did the arrows move the selection (no Mission Control/Spaces switch)?"),
        GuiTest("Alt+Space opens Spotlight",
                "Hold physical Alt and press Space (press Esc after).",
                "Did Spotlight open?"),
        GuiTest("Win+V clipboard history",
                "Hold physical Win and press V (press Esc after).",
                "Did the Maccy clipboard popup appear?"),
        GuiTest("Alt+Shift switches language",
                "Press and release physical Alt+Shift, then type a letter somewhere.",
                "Did the input language toggle (ABC <-> Hebrew)?"),
        GuiTest("Ctrl+Tab switches tabs",
                "In a browser with 2+ tabs, hold physical Ctrl and press Tab.",
                "Did it switch to the next tab?"),
        GuiTest("Alt+Left goes back in browser",
                "In a browser after navigating somewhere, hold physical Alt and press Left Arrow.",
                "Did the page go back?"),
        GuiTest("Win+Down restores a maximized window",
                "Maximize a window with Win+Up, then hold physical Win and press Down Arrow.",
                "Did the window return to its previous size (instantly)?"),
        GuiTest("Win+Down minimizes, Win+Up brings it back",
                "On a normal (not maximized) window press Win+Down, then press Win+Up.",
                "Did the window minimize and then come back?"),
        GuiTest("Dock click minimizes/restores",
                "Click the Dock icon of the app you're currently using, then click it again.",
                "Did its windows minimize, then come back?"),
        GuiTest("Win+D toggles Show Desktop",
                "Hold physical Win and press D, then press it again.",
                "Did the desktop show, then the windows come back?"),
        GuiTest("Win+E opens Finder",
                "Hold physical Win and press E.",
                "Did a Finder window open on your home folder?"),
        GuiTest("Win+Tab opens Mission Control",
                "Hold physical Win and press Tab (press Esc after).",
                "Did Mission Control appear?"),
        GuiTest("Alt+F4 quits app",
                "Focus a throwaway app (e.g. TextEdit), hold physical Alt and press F4 "
                "(Fn+F4 on the built-in keyboard).",
                "Did the app quit?"),
        GuiTest("Win+Shift+Left moves window between displays",
                "With a second display connected, hold physical Win+Shift and press Left Arrow "
                "(skip if only one display).",
                "Did the window jump to the other display?"),
        GuiTest("Ctrl+Space autocompletes in VS Code",
                "In a VS Code editor, hold physical Ctrl and press Space.",
                "Did the suggestions popup open (and NOT switch input language)?"),
        GuiTest("Finder: F2 renames",
                "In a Finder window, select a file and press F2 "
                "(Fn+F2 on the built-in keyboard). Press Escape after.",
                "Did the filename become editable?"),
        GuiTest("Finder: Del moves to Trash",
                "Select a throwaway file in Finder and press the Delete (forward delete) key.",
                "Did it move to the Trash?"),
        GuiTest("Finder: Ctrl+X / Ctrl+V moves a file",
                "Select a file, press physical Ctrl+X, open another folder, press physical Ctrl+V.",
                "Was the file moved (not copied)?"),
        GuiTest("Finder: Alt+Up goes to parent folder",
                "In a Finder window, hold physical Alt and press Up Arrow.",
                "Did it go up one folder?"),
        GuiTest("Finder: Alt+Left goes back",
                "After navigating between folders, hold physical Alt and press Left Arrow.",
                "Did it go back?"),
        GuiTest("Mouse wheel direction",
                "Scroll the mouse wheel down in any window.",
                "Did the page scroll down (Windows direction)?"),
        GuiTest("Red X quits app",
                "Open some app (e.g. TextEdit) and close its last window with the red X.",
                "Did the app fully quit (gone from Dock)?"),
    ]


def run_interactive(include_gui=True):
    print(bold("\nTerminal key tests") + dim("  (15s timeout per key; run inside Ghostty)"))
    results = []
    for t in terminal_key_tests():
        ok, detail = t.run()
        results.append((t.name, ok, detail))
        mark = green("PASS") if ok else red("FAIL")
        print(f"    {mark}  {t.name} {dim('- ' + detail)}")
    if include_gui:
        print(bold("\nGUI tests") + dim("  (answer y/n, or s to skip)"))
        for t in gui_tests():
            ok, detail = t.run()
            results.append((t.name, ok, detail))
            mark = {True: green("PASS"), False: red("FAIL"), None: yellow("SKIP")}[ok]
            print(f"    {mark}  {t.name}")
    failed = [r for r in results if r[1] is False]
    print()
    if failed:
        print(red(f"{len(failed)} interactive test(s) failed:"))
        for name, _ok, detail in failed:
            print(f"  - {name}: {detail}")
    else:
        print(green("All interactive tests passed (or were skipped)."))
    return not failed
