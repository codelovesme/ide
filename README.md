# ide — the codelovesme IDE, in the terminal

A standalone native Euglena app (no host, no membrane): open a folder, walk
it, edit its files. Centred on the code language — `.code` files are
coloured by the language's own lexer. v1 is deliberately small; it grows
step by step.

```sh
cdlvsm install ide          # also installs `code` if it is not there
cdlvsm ide ~/some/project   # or `cdlvsm-ide`; `--link` adds a bare `ide`
```

It opens the folder it is given, or the one it was started in. Ctrl+Q
quits; the terminal is given back as it was, even if the program dies.

## The screen

```
  File  View  Help                                   ide — project — src/a.code ●
 EXPLORER: PROJECT             a.code ●
 ▾ src                           1 | a comment
     a.code                      2 Greet { who } =>
 ▸ tests                         3     return Hi
                                                           Ln 2, Col 5    code
```

Row 0 is the menu bar — File, View, Help on the left, the folder and file
on the right. The last row is the status bar: messages, prompts ("Open
folder:", "Save changes?"), the cursor position and the language.

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
| Ctrl+S / Ctrl+W / Ctrl+Q | Save / Close File / Exit (each asks first if unsaved) |
| Ctrl+B | Show / hide the Explorer |
| Ctrl+Shift+E (Ctrl+0) / Ctrl+1 / F6 | Focus the Explorer / the editor / the other one |
| Alt+F Alt+V Alt+H, F10 | Menus: arrows, Enter, Escape |
| Ctrl+Z / Ctrl+Y | Undo / redo (typing is one step per run) |
| Ctrl+K Ctrl+S | Keyboard shortcuts |

In the editor: arrows, Home (first non-space, then column 0), End,
PageUp/PageDown, Ctrl+Home/End, Ctrl+Left/Right by word; Tab and Shift+Tab
indent by four spaces (code refuses tabs); Enter keeps the indentation and
adds a level after a block header (`… =>`, `if …`, `loop …` without a
comma). Ctrl+Shift+E and Ctrl+1 need a terminal that tells them apart from
Ctrl+E and 1 (kitty, foot, WezTerm, xterm, tmux with `extended-keys`); F6
always works.

## How it is built

| gene | what it is |
|---|---|
| `ide` | **all the state**, and what a key does to it — prompt, menu, command, then the focused pane |
| `keys` | which command a key runs; `ctrl+k` chords |
| `menu` | the menus, their keys, the bar and the dropdown |
| `layout` | the 9-slot layout |
| `tree` | the folder as flat rows (a handler cannot recurse, so opening a folder splices its children in) |
| `editor` | what a key does to a buffer |
| `render` | the whole screen from the state, as `tty` overlays |

Everything but `ide` is pure: a particle in, a particle out. State lives in
one gene because a gene's top level is its handlers' whole world. A handler
that fails puts `Error: …` in the status bar instead of stalling.

Organelles: `tty` (keys in, a screen out — only changed rows are written),
`syntax` (spans from code's lexer, still coloured while a file does not
lex), `fs`, `strings`, `env`.

## Developing

Needs only what anyone can install:

```sh
curl -sSf https://raw.githubusercontent.com/codelovesme/cdlvsm/main/install.sh | sh
cdlvsm install euglena      # brings code too
cdlvsm euglena install      # the organelles pinned in .code/lock.json
cdlvsm euglena test
IDE_FOLDER=~/some/project cdlvsm euglena run
```

## Releasing

A `v*` tag runs [the release workflow](.github/workflows/release.yml), which
does exactly the above on a clean machine, then
[tools/package.sh](tools/package.sh) lays out `ide-<tag>-x86_64-linux.tar.gz`
— [the launcher](bin/ide), `main.code`, the genes, and the organelles beside
`main.code` (the first place `code` looks), so the bundle needs nothing but
a `code` interpreter. The smoke test then runs the bundle in a terminal on
its own organelles before it is published.

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
