# macos-setup

Provisioner for my MacBook: makes macOS behave like Windows (keyboard, window
management, app switching, scrolling) and installs the tools I like. Originally
based on [this blog post](https://imoskvin.com/blog/macos-like-windows/), now
managed by a small dependency-free Python CLI that can detect drift, converge
the system, and verify that everything actually works.

```bash
./macsetup status     # what drifted from the desired setup?
./macsetup apply      # converge the system (idempotent)
./macsetup doctor     # status + conflicts, stale login items, permission problems
./macsetup test -i    # interactive verification (real keypresses + GUI checks)
./macsetup diff       # every check with expected/actual values
./macsetup adopt      # pull live edits of managed config files back into the repo
./macsetup list       # all managed components
```

Every command takes optional component names (`./macsetup apply karabiner maccy`).
`./install.sh` still works — it's now a wrapper for `./macsetup apply`.

macOS resets or overrides some of these settings over time (OS updates, app
updates, tools like Logi Options+ taking over a device). When something feels
off, run `./macsetup doctor` — it reports exactly which setting drifted, and
`./macsetup apply` puts it back.

---

## Components

| Component | What it manages |
|---|---|
| `brew` | GUI apps (Karabiner-Elements, Rectangle, AltTab, Maccy, Ghostty, UnnaturalScrollWheels, Swift Quit) and CLI tools |
| `system` | F-keys as F-keys, English locale, trackpad stays natural, snappy window animations, Writing Direction menu shortcuts |
| `input` | Keyboard layouts: English (ABC) + Hebrew enabled out of the box (Alt+Shift toggles) |
| `dock` | Windows-taskbar-style Dock: instant reveal at the bottom of *any* display (a pinned Dock only exists on one screen — macOS limitation), compact tiles, no magnification, minimize into app icon |
| `hotkeys` | macOS symbolic hotkeys: Ctrl+Arrow Mission Control/Spaces shortcuts off (they'd steal AltTab's arrow navigation); Ctrl+Space input switching off (Karabiner switches language directly, and VS Code needs Ctrl+Space for autocomplete); Show Desktop rebound to F17 for Win+D |
| `karabiner` | All key remapping. The Windows modifier swap is profile-wide (works on any keyboard automatically); the built-in keyboard and Apple external keyboards get Mac-layout overrides. Also installs the wake self-repair agent (see below) |
| `keybindings` | `DefaultKeyBinding.dict`: Page Up/Down move the cursor in Cocoa apps |
| `ghostty` | Ghostty config, icon, and the `ghostty-tmux-launch` script |
| `tmux` | `~/.tmux.conf` (oh-my-tmux) + `~/.tmux.conf.local` (prefix = C-a) |
| `zshrc` | Managed block in `~/.zshrc`: Home/End keybindings, LC_TIME |
| `alttab` | Hold Control (= physical Alt), arrow keys, hidden menu bar icon, lists minimized + hidden windows like Windows' Alt+Tab (note: AltTab's `showMinimizedWindows`/`showHiddenWindows` are an enum where **0 = show**, 1 = hide — not booleans) |
| `maccy` | Clipboard history on Win+V (hotkey is Option+V set directly in Maccy — no Karabiner rule involved) |
| `rectangle` | Window snapping shortcuts, written straight to defaults (no manual import needed) |
| `scroll` | UnnaturalScrollWheels: invert mouse wheel only, trackpad untouched |
| `finder` | Explorer-like Finder: all extensions, path/status bar, folders first, list view, search current folder |
| `swiftquit` | Swift Quit settings + running check |
| `dockdoor` | DockDoor: click the active app's Dock icon to minimize, click again to restore (Windows taskbar); hover previews with controls embedded in the preview frame. Settings live in `config/dockdoor/settings.json` — tune them in DockDoor's UI, then `./macsetup adopt dockdoor` |
| `scripts` | Helper scripts in `~/.local/bin` (tmux launcher) |
| `login` | Login items for all of the above |

`./macsetup adopt` pulls live state back into the repo — for the file-based
components (`keybindings`, `ghostty`, `tmux`, `scripts`) and for `dockdoor`,
whose settings are snapshotted as JSON. Tweak things in the app's own UI, run
adopt, and the repo stays the source of truth.

---

## How the keyboard remapping works

On a Windows keyboard the bottom-left modifiers are `Ctrl | Win | Alt`; on the
Mac's built-in keyboard they are `Control | Option | Command`. Karabiner
device-scoped `simple_modifications` swap them so that both keyboards end up
with the same *logical* layout:

| Physical key | Built-in Mac keyboard | External Windows keyboard |
|---|---|---|
| Ctrl | → Command | → Command |
| Win / Cmd | → Control (acts as Alt) | → Option (acts as Win) |
| Alt / Option | → Option (acts as Win) | → Control (acts as Alt) |

So in every complex rule below: **physical Ctrl = `command`, physical Win =
`option`, physical Alt = `control`**.

The Windows-layout swap lives in the profile-level `simple_modifications`, so
it applies to **any keyboard, current or future, with zero setup** — Karabiner
compiles device-scoped modifications before profile-level ones (first-match),
making profile entries a pure fallback. The built-in keyboard carries a
device-scoped Mac-layout override in the template (including an identity
mapping that keeps Option as Option), and `./macsetup apply` generates the
same override for any connected Apple-vendor external keyboard, since those
have a Mac layout too.

### Complex rules

| Rule | What it does |
|---|---|
| Win+Arrow → Ctrl+Option+Arrow | Window snapping via Rectangle: Left/Right halves, Up maximize, Down restore |
| Win+Shift+Left/Right → Ctrl+Option+Cmd+Arrow | Move window to previous/next display (Rectangle) |
| Terminal: Ctrl+Arrow → Esc b/f | Word-by-word navigation in Ghostty/Terminal.app |
| Ctrl+Arrow → Option+Arrow | Word navigation everywhere else (Shift allowed for selection) |
| Terminal: Ctrl+A/C/D/E/K/L/R/U/Z → real control chars | SIGINT, EOF, clear, etc. — Ctrl+Shift+C/V stay copy/paste |
| Win+1/2/3 | Launch Chrome / Ghostty / IPython |
| Media keys → F1–F12 | External keyboard media keys become function keys |
| Alt+F4 → Cmd+Q, Ctrl+F4 → Cmd+W | Quit app / close tab or window |
| F11 → Cmd+Ctrl+F | Fullscreen toggle |
| Win+D → F17 | Toggles macOS Show Desktop (hotkey rebound to F17; press again to bring windows back) |
| Win+E | Open home folder in Finder |
| Win+Tab | Mission Control (Task View) |
| PrintScreen (or F13) | Region screenshot to the clipboard; Win+PrintScreen = the whole display **the cursor is on**, to the clipboard. Both run `macsetup-screenshot`, because macOS's own whole-screen shortcut only ever captures the Main Display — on a multi-display setup it silently grabs the wrong screen. Nothing is written to the Desktop; `system` also pins `com.apple.screencapture target=clipboard` |
| Finder: F2 / Del / Ctrl+X,V / Alt+Up | Rename / move to Trash / cut-paste files / parent folder |
| Ctrl+Space | Autocomplete in VS Code / Antigravity, blocked elsewhere; Alt+Space → Cmd+Space opens Spotlight |
| Alt+Shift (tap) | Toggle input source ABC ↔ Hebrew (`select_input_source`, 2s tap window) |
| Ctrl+LeftShift / Ctrl+RightShift (tap) | Paragraph direction LTR / RTL (right-aligned for Hebrew), like Windows. Sends Cmd+Opt+Ctrl+L/R, which `NSUserKeyEquivalents` binds to the Writing Direction menu items (Cocoa apps: TextEdit, Notes, Mail, Pages…). Chrome has no such menu — use right-click → Writing Direction there |
| Ctrl+Backspace → Option+Backspace | Delete previous word |
| Terminal: DEL → forward delete | Forward delete works in terminals |
| Cmd+Shift+Esc | Activity Monitor (Task Manager) |
| Terminal: Home/End pass through | Shell handles them via zsh bindkeys (see below) |
| Home/End → Cmd+Left/Right (+Cmd for document) | Windows-style line/document navigation elsewhere |
| Win+L → Cmd+Ctrl+Q | Lock screen |
| Ctrl+Tab / Ctrl+Shift+Tab | Next/previous tab |
| Alt+F3 → Option+F3 | Select All Occurrences in VS Code / Antigravity |
| AltTab tracking variable | Sets `alttab_open` while physical Alt+Tab is held, so the Alt+Arrow rules below never steal AltTab's arrow navigation |
| Alt+Left/Right → Cmd+[ / Cmd+] | Back/forward in Chrome, Safari, Firefox, Finder |
| Alt+Up/Down → Option+Up/Down | Move line up/down in VS Code / Antigravity (Shift allowed = copy line) |

Ordering constraints encoded in the template:

- Terminal-scoped rules come **before** their generic counterparts (Karabiner
  is first-match). Note manipulator output is *not* re-processed by later
  rules — each physical key event matches at most one manipulator.
- The AltTab tracking rule (which matches a bare Control press) comes **after**
  the Alt+Shift input-source rule, or it would swallow the Control press that
  rule needs.
- Finder cut/paste works via a `finder_cut` variable: Ctrl+X copies and arms
  it, Ctrl+V then pastes-as-move (Cmd+Option+V); plain Ctrl+C disarms it.

### Sleep/wake self-repair

Karabiner can come back from sleep half-working: it tears down and recreates
its virtual keyboard, and afterwards *simple* modifications still apply while
*complex* modifications silently stop firing. The keys are still remapped, but
Win+Arrow, Ctrl+Arrow, Ctrl+Backspace (which then falls through to macOS's
delete-to-start-of-line) and the language toggle all do nothing. Nothing in
Karabiner's config or logs reports it — reloading the config does not help, but
restarting its services does.

`macsetup apply karabiner` installs a LaunchAgent
(`com.macsetup.karabiner-wake`) that repairs this automatically. launchd has no
wake trigger, so it runs on a `StartInterval`: the timer expires while the Mac
sleeps and launchd fires the job right after wake. The script
(`config/bin/macsetup-karabiner-wake`) then restarts Karabiner's agents exactly
once per wake, reading `kern.waketime` and keeping the last handled wake in
`~/.local/state/macsetup/karabiner-wake`.

Details that matter: `kern.waketime` is `0` until the first real wake, so a
fresh boot never triggers a restart; the script waits 10s after wake so a
restart can't strand a key down; it records the wake before acting so a failure
can't loop; and `apply` seeds the state file, so installing the agent never
restarts Karabiner as a side effect.

### Home/End and the tmux C-a prefix

tmux's prefix is `C-a` (screen-style, set in `.tmux.conf.local`). Home used to
be remapped to Ctrl+A in terminals, so every Home press was eaten as a tmux
prefix and had to be pressed twice — worst inside ssh. Now Home/End pass
through to the terminal untouched, and the zsh side binds the escape sequences
(`^[[H`/`^[OH`/`^[[1~` etc., covering both direct-Ghostty and through-tmux
encodings) in the managed `~/.zshrc` block. Remote Linux boxes bind these by
default (`/etc/inputrc`), so Home/End work first-press over ssh too.

### AltTab

AltTab listens directly on Control+Tab (physical Alt+Tab) — no Karabiner rule
converts it, so the held modifier is genuine and arrow-key navigation works.
The `hotkeys` component disables macOS's own Ctrl+Arrow shortcuts (Mission
Control, Spaces) because they would swallow the arrows while Control is held.
The hold shortcut is stored by AltTab 10.x as a ShortcutRecorder blob;
`./macsetup apply` writes it with PlistBuddy from `config/alttab/holdShortcut.plist`.

### Scrolling

macOS "natural" scrolling stays on globally (trackpad behaves like a Mac).
UnnaturalScrollWheels inverts **mouse wheels only**, giving Windows direction on
any mouse. Scroll Reverser and per-device inversion in Logi Options+ do the
same job — don't run two of them, or the wheel gets double-flipped.
`./macsetup doctor` warns if Logi Options+ has the wheel set to Inverted or if
a duplicate scroll app is installed.

---

## Fresh machine bootstrap

```bash
# 1. Install Homebrew (https://brew.sh), then:
git clone git@github.com:Avidanborisov/macos-setup.git
cd macos-setup
./macsetup apply
```

Then the steps only a human can do:

1. **Accessibility** (System Settings → Privacy & Security → Accessibility):
   Karabiner, Rectangle, AltTab, Swift Quit, Maccy
2. **Input Monitoring**: karabiner_grabber, karabiner_observer
3. If macOS blocks background items: System Settings → General → Login Items
4. VS Code: `"editor.mouseWheelZoom": true` in settings.json
5. Log out/in (or restart) so every app picks up the keyboard changes

Finish with `./macsetup doctor` and `./macsetup test -i`.

---

## Testing

- `./macsetup test` — every automated check (files, defaults, processes,
  login items, Karabiner device coverage).
- `./macsetup test -i` — run inside Ghostty. Terminal key tests put the tty in
  raw mode and assert on the actual bytes your keypress produces after the
  whole Karabiner → Ghostty → tmux pipeline (Home, End, Ctrl+Arrow,
  Ctrl+Backspace, Ctrl+C/D, DEL, Page Up). GUI tests (snapping, AltTab,
  Spotlight, Maccy, language toggle, scroll direction, red-X quit) ask for a
  y/n confirmation.
- `./macsetup test -i --keys-only` — just the terminal key tests.

---

## Keyboard cheat sheet

| Windows shortcut | Effect |
|---|---|
| Ctrl+C/V/X/Z | Copy/Paste/Cut/Undo |
| Ctrl+Left/Right (+Shift) | Move (select) by word |
| Ctrl+Backspace | Delete previous word |
| Win+Left/Right/Up | Snap left/right, maximize (F11 for fullscreen) |
| Win+Down | Restore (un-maximize / un-snap) |
| Click Dock icon of active app | Minimize; click again to restore |
| Win+Shift+Left/Right | Move window to previous/next display |
| Alt+Tab (+ arrows) | Window switcher |
| Alt+F4 / Ctrl+F4 | Quit app / close tab |
| Win+Tab | Mission Control |
| Win+E | Finder (home folder) |
| Ctrl+Space | Autocomplete (VS Code / Antigravity) |
| Ctrl+Tab / Ctrl+Shift+Tab | Next/previous tab |
| Alt+Left/Right | Back/forward (browsers) |
| Alt+Up/Down | Move line (VS Code / Antigravity) |
| Win+D | Show desktop (toggle) |
| PrintScreen / Win+PrintScreen | Region snip to clipboard / whole screen to clipboard |
| F2 / Del / Ctrl+X,V / Alt+Up/Left/Right | In Finder: rename / delete / cut-paste / navigate |
| Alt+Space | Spotlight |
| Alt+Shift (tap) | Switch language (ABC ↔ Hebrew) |
| Ctrl+LeftShift / Ctrl+RightShift (tap) | Paragraph direction LTR / RTL (Hebrew right-align) |
| Win+V | Clipboard history (Maccy) |
| Win+1/2/3 | Chrome / Ghostty / IPython |
| Win+L | Lock screen |
| Cmd+Shift+Esc | Activity Monitor |
| F11 | Fullscreen |
| Home/End (+Ctrl) | Line (document) start/end |
| Page Up/Down | Move cursor by page |
| § (Mac keyboard) | ` and ~ |

Terminal (Ghostty / Terminal.app): Ctrl+C/Z/D/L are real control characters,
Ctrl+Shift+C/V copy/paste, Ctrl+Left/Right word navigation, Home/End line
start/end (single press, including in ssh/tmux), DEL forward-deletes.

---

## Known limitations

| Issue | Why | Workaround |
|---|---|---|
| Ctrl+C/R/Z in VS Code's integrated terminal | Karabiner can't tell the terminal panel from the editor in the same app | Alt+C/R/Z works (physical Alt sends Control); or rebind in VS Code |
| Ctrl+scroll zoom in browsers | Karabiner can't intercept scroll events | Ctrl+= / Ctrl+- page zoom |
| Alt+<key> app shortcuts in unscoped apps | Physical Alt sends Control, apps expect Option | Rules exist for VS Code/Antigravity/browsers; add app-scoped rules as needed |
| F11 on the built-in keyboard | No F11 on Touch Bar models | Fn+F11 or Ctrl+Cmd+F |
| Finder Ctrl+X while renaming a file | Karabiner can't tell rename-edit mode from normal browsing, so Ctrl+X/V act on the file, not the selected text | Use Cmd+X/V equivalents via right-click, or finish the rename first |
| Minimizing a **Finder** window leaves a tile next to the Trash | macOS special-cases Finder: it ignores "minimize into application icon" (verified — regular apps like TextEdit honor it, Finder never does). No setting changes this. | Close Finder windows with Ctrl+W when done; the tile disappears once the window is restored. Alt+Tab lists minimized windows, so they stay reachable. |
| Logi Options+ | Manages the mouse independently; can fight UnnaturalScrollWheels | Keep its scroll direction on "Standard"; doctor warns otherwise |
