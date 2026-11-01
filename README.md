# ide — the codelovesme IDE, in the terminal

A standalone native Euglena app (no host, no membrane): open a folder, walk
it, edit its files. Centred on the code language — `.code` files are
coloured by the language's own lexer. v1 is deliberately small; it grows
step by step.

```sh
cdlvsm install ide
cdlvsm ide ~/some/project   # or `cdlvsm-ide`; `--link` adds a bare `ide`
```

It opens the folder it is given, or the one it was started in. Ctrl+Q
quits; the terminal is given back as it was, even if the program dies.

## The screen

```
  File  View  Settings  Help                         ide — project — src/a.code ●
 EXPLORER: PROJECT             a.code ●
 ▾ src                           1 | a comment
     a.code                      2 Greet { who } =>
 ▸ tests                         3     return Hi
                                                           Ln 2, Col 5    code
```

Row 0 is the menu bar — File, View, Settings, Help on the left, the folder and file
on the right. The last row is the status bar: messages, prompts ("Open
folder:", "Save changes?"), the cursor position and the language.

### Everything is a tab, anywhere

Files, the Explorer and terminals are all tabs, and every group of tabs
sits in one of the nine slots. **Move Tab** (View menu, or Ctrl+K M) asks
where — `l r t b c tl tr bl br` — and takes the tab there, beside whatever
is in that slot already; commands `view.moveTab.<slot>` do it in one key
(keybindings.json). So the explorer can be a tab in the center, a terminal
can sit on the right, two files can share a group or stand side by side.
The explorer is one tab like the rest.

### Pane keys

| | |
|---|---|
| Ctrl+B | the Explorer |
| Ctrl+J (or Ctrl+\`) | the terminal |
| Ctrl+E | the files |

Each works the same way: if the pane is not shown, it is opened and given
the keys; if it is shown, it is given the keys; if it already has them, it
is put away. Terminals put away keep running and files keep their unsaved
edits and undo — the key brings them back where they were (so does opening
a file, or a new terminal). The pane keys work from inside a terminal too.
Ctrl+J needs a terminal that tells it apart from Enter (kitty, foot,
WezTerm, Ghostty, Alacritty); elsewhere Ctrl+\` does the same.

### The terminal

Ctrl+J / Ctrl+\` (View > Terminal) opens one on the right, full height, in
the open folder, so the code keeps all its rows (see Pane keys); View > New
Terminal (or Ctrl+K T) adds another, and Ctrl+T in a terminal another
beside it. `terminal.location` (`l r t b c tl tr bl br`) puts new ones
elsewhere; moving a terminal tab (Move Tab) sets it too. It is your shell (`$SHELL`, or `terminal.integrated.shell`),
on a real pseudo-terminal, with its colours. While it has the keys, every
key goes to the shell — Ctrl+C, Ctrl+E, Ctrl+W are the shell's — except the
commands listed in `terminal.integrated.commandsToSkipShell` (F6, Ctrl+Tab,
the menus, Ctrl+Q, the pane keys …). `exit` closes its tab. Outside the terminal Ctrl+Space remains an alias for opening it; inside a
terminal Ctrl+Space goes to the running program (for example Mike push-to-talk). Shift+PgUp / Shift+PgDn scroll
back through what went off the top (typing returns to the live screen). A
program that asks for them (an editor inside) gets Ctrl+Tab, Ctrl+J and the
rest whole, as far as the terminal the ide runs in passes them on — see
[console](https://github.com/codelovesme/console).

### AI: in a terminal

The ide has no AI of its own. Claude Code, Codex and Mike are command-line
programs; run them in a terminal tab like any other — `claude`, `codex`,
`mike-cli` — on the right, beside the code. Each signs in, picks its model
and keeps its conversations itself, so a new version of one never needs a
new ide. (0.22 and before had an AI chat built in; 0.23 took it out, with
its settings, keys and Settings > Account. An old settings.json or
keybindings.json that still names them opens without a complaint.)

### Assistants know and control their IDE

In an IDE terminal, ordinary `claude` and `codex` commands receive a local MCP
connection for this IDE instance. Ask “move my terminal to the left” or “make
my terminal a little bigger”. `ide_state`, `ide_move_terminal` and
`ide_resize_terminal` act on the terminal where the assistant was launched,
even if another tab has since taken focus. User instructions and other MCP
servers stay configured as before. Shell aliases/functions or an absolute CLI
path can bypass the launch adapter; use the executable on the IDE terminal's
PATH for automatic integration.

Mike CLI with IDE context support receives the same session context on every
message. Its existing local terminal tool runs the control client through
Mike's normal confirmation/approval flow; Mike does not need a separate MCP
client. Older Mike clients continue to chat but do not receive this context.

You can also inspect or change the layout yourself in that terminal:

```sh
ide-control state
ide-control move --slot left
ide-control move --slot bottom
ide-control resize --delta 2     # grow; -2 shrinks
```

This uses Python 3 (standard library only) and a loopback-only HTTP endpoint
with a random per-instance credential stored in a private temporary directory.
Session and terminal identifiers select the target; they are not credentials.
No control key is included in model context or command-line arguments. Normal
exit removes the descriptor; a crash can leave an inert descriptor, which
cannot authorize a different IDE session. Connections are Linux-local, and
clients reject listeners belonging to another OS user.

Moves support all nine slots. Resizing changes the shared side track in
columns (left/right and corners) or rows (top/bottom), within the screen's
limits; other panes on that track resize too. The center fills remaining space
and cannot resize independently. Replies report the actual pane dimensions.
A hidden or closed terminal returns an explicit error for movement/resizing.

See [the control protocol](docs/ide-control.md) for adapters and session lifecycle.

### Tabs and editor groups

Every open file has a tab; the active tab's file is shown, and opening a
file that is already open brings its tab back as it was left — edits,
cursor and undo. Split Editor (Ctrl+\\, or View) opens the file again in
the group on the right. Exit asks once about
every file with unsaved changes. (The same file in both groups is two
copies for now: an edit in one does not show in the other.)

### Panes: nine slots

The body is a 3×3 grid — `tl t tr / l c r / bl b br`
([src/layout.gene.code](src/layout.gene.code)). A column or row with
nothing in it takes no room, and an empty slot is taken by a neighbour
growing into it, as long as that neighbour stays a rectangle: a side goes to
its corner, then the center; a top or bottom to the center, then its
corners; a corner to its side. So the tree alone fills the screen; the tree
and a file are left and center, the center covering the right too. Today
there are two panes — the Explorer (left, or right from the View menu) and
the editor (center); the grid is ready for more.

## Keys (VS Code's)

| | |
|---|---|
| Ctrl+N | New File… — in the folder picked in the Explorer (a file picked: its folder; nothing picked, or the Explorer hidden: the root). Only the name is asked; a name ending in `/` makes a folder |
| Ctrl+P | Go to File…: the project's files that match what is typed (the name's own letters first); ↑/↓ pick, Enter opens |
| Ctrl+F | Find in the file: as it is typed, the next match is selected and counted ("2 of 5"); Enter the next, Shift+Enter the one before, Escape leaves the cursor there |
| Ctrl+C / Ctrl+X / Ctrl+V | Copy / cut / paste the selection (Shift+arrows, Ctrl+A), through the desktop's clipboard. In a terminal they are the shell's |
| Ctrl+H / Ctrl+G | Replace (what, then with what — every one, one undo step) / Go to Line (`12`, or `12:5`). A terminal that sends Ctrl+Backspace as ^H makes Ctrl+H Ctrl+Backspace there; Edit > Replace… still works |
| Ctrl+Backspace / Ctrl+Delete | Delete a word back / forward |
| Ctrl+D | The word at the cursor; again, the next same text too, with a cursor of its own — typing, Enter, Backspace and the moves act at every cursor; Escape keeps one |
| Alt+↑ / Alt+↓ | Move the line, or the selected lines, up / down |
| Ctrl+Shift+Alt+↑ / ↓ | Copy the line, or the selected lines, above / below (VS Code's keys on Linux) |
| Shift+Alt+↑ / ↓ | Another cursor on the line above / below (Ctrl+Shift+arrows select: ←/→ by word, ↑/↓ by line) |
| Ctrl+/ | Comment the line(s) out, or back in, with the language's mark (`#`, `//`, `--` …) |
| Ctrl+K Ctrl+O | Open Folder… |
| Ctrl+S / Ctrl+W / Ctrl+Q | Save / close the tab / Exit (each asks first if unsaved) |
| Alt+← / Alt+→ | Go Back / Go Forward: where the cursor has been — another file, or a jump of 10 lines or more (View menu too) |
| Ctrl+Tab / Ctrl+Shift+Tab (or Shift+Tab) | Next / previous tab, round and round, as in a browser — GNOME's terminals send Ctrl+Tab as a plain Tab, so there only Shift+Tab arrives. In a terminal tab Shift+Tab is the shell's |
| Ctrl+\\ | Split Editor: the file again, in a second editor on the right |
| Ctrl+B / Ctrl+J / Ctrl+E | The Explorer / the terminal / the files: open and focus; focus; put away (see Pane keys) |
| Ctrl+0 / Ctrl+1 / Ctrl+2 | Focus the Explorer / the first / the second editor |
| F6 | Explorer, then each editor, round again |
| Alt+F Alt+V Alt+S Alt+H, F10 | Menus: arrows, Enter, Escape |
| Ctrl+Z / Ctrl+Y | Undo / redo (typing is one step per run) |
| Ctrl+K Ctrl+S | Keyboard shortcuts |
| Ctrl+, | Settings (settings.json) |
| Ctrl+K and an arrow | Move the focused side's edge (the left grows with →, the bottom with ↑) |
| Ctrl+K M | Move the tab to another place |
| (View > Word Wrap) | Long lines go on in the rows below (`editor.wordWrap`: "on" / "off") |
| Ctrl+K T | A new terminal |
| Ctrl+T | Another terminal, beside the one that has the keys |
| Ctrl+Shift+N | New Window: another ide on this folder |

In the editor: brackets and quotes close themselves, the matching bracket is lit; arrows, Home (first non-space, then column 0), End,
PageUp/PageDown, Ctrl+Home/End, Ctrl+Left/Right by word; Tab indents by
four spaces and Ctrl+K Shift+Tab takes a level back (code refuses tabs); Enter keeps the indentation and
adds a level after a block header (`… =>`, `if …`, `loop …` without a
comma). Ctrl+1 needs a terminal that tells it apart from 1 (kitty, foot, WezTerm,
xterm, tmux with `extended-keys`); F6 always works.

### The mouse

A click puts the cursor there; a drag selects; a double click selects the
word, a triple the line; Shift+click selects to the click, Alt+click adds a
cursor. The wheel scrolls the file or terminal under it. A click on a
tab shows it, in the explorer opens the row, on a menu title opens the
menu, on an item runs it. It needs a `tty` module that reports the mouse
(code's tty after 2.21.1); with an older one the ide works as before,
keys only. While the ide has the mouse, the terminal's own selection is
Shift+drag (in most terminals).


## Settings

Like VS Code, a JSON file: `settings.json` in `$XDG_CONFIG_HOME/codelovesme-ide/`
(`~/.config/codelovesme-ide/` when that is not set). Ctrl+, or Settings >
Settings opens it; saving it applies it. Hiding, moving or resizing the
explorer writes it for you.

```json
{
  "workbench.sideBar.visible": true,
  "workbench.sideBar.location": "left",
  "workbench.layout.left": 30,
  "workbench.layout.right": 40,
  "workbench.layout.top": 10,
  "workbench.layout.bottom": 12,
  "terminal.integrated.shell": "",
  "terminal.location": "r",
  "editor.wordWrap": "off",
  "terminal.integrated.commandsToSkipShell": ["terminal.toggle", "focus.next", "…"]
}
```

(`workbench.sideBar.width` and `workbench.panel.height`, the names before
0.6, are still read.)

A value that is missing or wrong falls back to its default, and the status
bar says which.

## Keyboard shortcuts

Like VS Code, `keybindings.json` beside `settings.json`, on top of the
defaults. Settings > Keyboard Shortcuts (JSON) opens it; saving it applies it.

```json
[
  { "key": "ctrl+shift+b", "command": "view.explorer" },
  { "key": "ctrl+b", "command": "-view.explorer" },
  { "key": "ctrl+j ctrl+q", "command": "app.quit" }
]
```

A later entry wins; `-command` takes that key's default away; a key with a
space is a chord. Keys can be written in any case, modifiers in any order.
Ctrl+K Ctrl+S lists every command with its id and the keys that run it, and
the menus show the keys in use. A bad entry is left out and the status bar
says which. (Some keys cannot be told apart by a terminal — Ctrl+J is
Enter, Ctrl+I is Tab, Ctrl+M is Enter.)

## How it is built

| gene | what it is |
|---|---|
| `ide` | **all the state**, and what a key does to it — prompt, menu, command, then the focused pane |
| `keys` | the key table: defaults + keybindings.json, chords, how keys are shown |
| `menu` | the menus, their keys, the bar and the dropdown |
| `layout` | the 9-slot layout |
| `tree` | the folder as flat rows (a handler cannot recurse, so opening a folder splices its children in) |
| `editor` | what a key does to a buffer |
| `render` | the whole screen from the state, as `tty` overlays |
| `settings` | settings.json read and checked, and written back |
| `tabs` | what is open where: groups in slots, their tabs (files, the explorer, terminals) |

Everything but `ide` is pure: a particle in, a particle out. State lives in
one gene because a gene's top level is its handlers' whole world. A handler
that fails puts `Error: …` in the status bar instead of stalling.

Organelles: `tty` (keys in, a screen out — only changed rows are written),
`syntax` (spans from code's lexer, still coloured while a file does not
lex), `fs` (twice: the open folder, and the settings folder), `json`,
`strings`, `env`, `pty` (the terminals), `process` (ripgrep or git for
Ctrl+P, and New Window), `window` (the desktop's clipboard).

## Developing

Needs only what anyone can install:

```sh
curl -sSf https://raw.githubusercontent.com/codelovesme/cdlvsm/main/install.sh | sh
cdlvsm install euglena      # brings code too
cdlvsm euglena install      # the organelles pinned in .code/lock.json
tools/organelles.sh         # …laid out where the ide links them from
cdlvsm euglena test
IDE_FOLDER=~/some/project cdlvsm euglena run
```

## Releasing

A `v*` tag runs [the release workflow](.github/workflows/release.yml), which
does exactly the above on a clean machine. Then
[tools/package.sh](tools/package.sh) builds the ide as a program (`code
build`) and lays out `ide-<tag>-x86_64-linux.tar.gz`: the program, [its
launcher](bin/ide) and the organelles beside it. It needs no
`code` interpreter to run. The smoke test proves that — it runs the bundle
with no `code` on the machine and no module cache —
before it is published.

The organelles are linked while the ide runs (`Organelles` in
[src/ide.gene.code](src/ide.gene.code)), not when it is built: a top-level
`link` would build in the full path each one has on the building machine.
The launcher starts the program in its own folder, where they are, and
tells it which folder to open.

## Tests

`euglena test` — [tests/layout.code](tests/layout.code) (every slot, and
the shapes above), [tests/editor.code](tests/editor.code) (the keys on a
buffer), [tests/ide.code](tests/ide.code) (a folder opened, walked, a file
edited, undone, saved, the menu, the prompts, a frame drawn, terminals
opened, moved and put away), [tests/keys.code](tests/keys.code) and
[tests/tabs.code](tests/tabs.code), all without a terminal.

In a real terminal: `python3 tools/smoke.py` (from a checkout) or
`python3 tools/smoke.py <bundle>/ide` — a pty, keys pressed, the screen read
back by [tools/drive.py](tools/drive.py), a small emulator for what `tty`
sends (no tmux or pyte needed).

## Next

Find across the project, diagnostics from the language server,
extensions.

### Development key-release support (ticket 188, unreleased)

Key releases pass from the outer terminal through tty and the IDE to the
integrated terminal. Ctrl+Space inside that terminal is reserved for its
program; Ctrl+J and Ctrl+backtick still toggle the panel. A held voice shortcut
keeps its original terminal target if focus moves before the key is released.

The current IDE bundle still uses ABI 1. Build matching development modules
without changing the installed compiler or public lockfile:

```sh
python3 ../code/scripts/build-key-event-modules.py --abi 1 --out organelles
```

This explicitly uses the v2.14.5 code-native/runtime snapshot for ABI 1 and
current source window/pty/tty implementations. The outer console needs the
updated modules too. Keep these modules when laying out a development package;
the public pinned release alone does not provide this support.
