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
The explorer is one tab like the rest: Ctrl+B takes it away and brings it
back where it was.

### The terminal

Ctrl+\` (View > Terminal) opens one at the bottom, in the open folder, and
moves the keys between it and the files; View > New Terminal (or Ctrl+K T)
adds another. It is your shell (`$SHELL`, or `terminal.integrated.shell`),
on a real pseudo-terminal, with its colours. While it has the keys, every
key goes to the shell — Ctrl+C, Ctrl+E, Ctrl+W are the shell's — except the
commands listed in `terminal.integrated.commandsToSkipShell` (F6, Ctrl+Tab,
the menus, Ctrl+Q, Ctrl+\` …). `exit` closes its tab. Most terminals send
Ctrl+\` as Ctrl+Space, which is bound too. Not yet: scrollback, the mouse.

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
| Ctrl+K Ctrl+O | Open Folder… |
| Ctrl+S / Ctrl+W / Ctrl+Q | Save / close the tab / Exit (each asks first if unsaved) |
| Ctrl+Tab / Ctrl+Shift+Tab (or Ctrl+PgDn / Ctrl+PgUp) | Next / previous tab — many terminals send Ctrl+Tab as plain Tab; Ctrl+PgDn always works |
| Ctrl+\\ | Split Editor: the file again, in a second editor on the right |
| Ctrl+B | Show / hide the Explorer |
| Ctrl+Shift+E (or Ctrl+E, Ctrl+0) / Ctrl+1 / Ctrl+2 | Focus the Explorer / the first / the second editor |
| F6 | Explorer, then each editor, round again |
| Alt+F Alt+V Alt+S Alt+H, F10 | Menus: arrows, Enter, Escape |
| Ctrl+Z / Ctrl+Y | Undo / redo (typing is one step per run) |
| Ctrl+K Ctrl+S | Keyboard shortcuts |
| Ctrl+, | Settings (settings.json) |
| Ctrl+K and an arrow | Move the focused side's edge (the left grows with →, the bottom with ↑) |
| Ctrl+K M | Move the tab to another place |
| Ctrl+\` (Ctrl+Space) / Ctrl+K T | The terminal / a new terminal |

In the editor: arrows, Home (first non-space, then column 0), End,
PageUp/PageDown, Ctrl+Home/End, Ctrl+Left/Right by word; Tab and Shift+Tab
indent by four spaces (code refuses tabs); Enter keeps the indentation and
adds a level after a block header (`… =>`, `if …`, `loop …` without a
comma). Most terminals send Ctrl+Shift+E as Ctrl+E, so that works too.
Ctrl+1 needs a terminal that tells it apart from 1 (kitty, foot, WezTerm,
xterm, tmux with `extended-keys`); F6 always works.

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
`strings`, `env`, `pty` (the terminals).

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
launcher](bin/ide), and the seven organelles beside it. It needs no `code`
interpreter to run. The smoke test proves that — it runs the bundle with no
`code` on the machine and no module cache — before it is published.

The organelles are linked while the ide runs (`Organelles` in
[src/ide.gene.code](src/ide.gene.code)), not when it is built: a top-level
`link` would build in the full path each one has on the building machine.
The launcher starts the program in its own folder, where they are, and
tells it which folder to open.

## Tests

`euglena test` — [tests/layout.code](tests/layout.code) (every slot, and
the shapes above), [tests/editor.code](tests/editor.code) (the keys on a
buffer), [tests/ide.code](tests/ide.code) (a folder opened, walked, a file
edited, undone, saved, the menu, the prompts, and a frame drawn), all
without a terminal.

In a real terminal: `python3 tools/smoke.py` (from a checkout) or
`python3 tools/smoke.py <bundle>/ide` — a pty, keys pressed, the screen read
back by [tools/drive.py](tools/drive.py), a small emulator for what `tty`
sends (no tmux or pyte needed).

## Next

Tabs and more than one file, Ctrl+P, find, the clipboard, the mouse,
resizing panes, a terminal pane in the bottom slot, diagnostics from the
language server, extensions.
