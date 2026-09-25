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
| Ctrl+L | the AI chat |
| Ctrl+E | the files |

Each works the same way: if the pane is not shown, it is opened and given
the keys; if it is shown, it is given the keys; if it already has them, it
is put away. Terminals put away keep running and files keep their unsaved
edits and undo — the key brings them back where they were (so does opening
a file, or a new terminal). The pane keys work from inside a terminal too.
Ctrl+J needs a terminal that tells it apart from Enter (kitty, foot,
WezTerm, Ghostty, Alacritty); elsewhere Ctrl+\` does the same.

### The terminal

Ctrl+J / Ctrl+\` (View > Terminal) opens one at the bottom, in the open
folder (see Pane keys); View > New Terminal (or Ctrl+K T)
adds another. It is your shell (`$SHELL`, or `terminal.integrated.shell`),
on a real pseudo-terminal, with its colours. While it has the keys, every
key goes to the shell — Ctrl+C, Ctrl+E, Ctrl+W are the shell's — except the
commands listed in `terminal.integrated.commandsToSkipShell` (F6, Ctrl+Tab,
the menus, Ctrl+Q, the pane keys …). `exit` closes its tab. Most terminals send
Ctrl+\` as Ctrl+Space, which is bound too. Shift+PgUp / Shift+PgDn scroll
back through what went off the top (typing returns to the live screen). A
program that asks for them (an editor inside) gets Ctrl+Tab, Ctrl+J and the
rest whole, as far as the terminal the ide runs in passes them on — see
[console](https://github.com/codelovesme/console). Not yet: the mouse.

### The AI chat

Ctrl+L (View > AI Chat) opens it, on the right until you move it (Move
Tab, like any tab — it remembers where). Ask about the project in your own
words: it is sent what you are looking at, so "this function", "here" and
"why did that fail?" need no file named —

- the open file, the lines round the cursor, the other tabs, the places
  you just edited, the terminal's last lines, git's branch and changes;
- the project's own instructions: `AGENTS.md`, `CLAUDE.md`, `.cursorrules`,
  `.github/copilot-instructions.md`, `.ide/instructions.md`, `.ide/memory.md` — at the root
  and in each folder down to the open file;
- a map of the project: every file (ripgrep's list, so `.gitignore` holds),
  and the names each one defines;
- and tools it uses itself, step by step, each shown in grey: list a
  folder, read a file, search (ripgrep), find files, git diff.

**It changes nothing without you.** An edit or a new file it proposes
opens as a tab of its own — removed lines red, added green — and waits:
`a` (or Enter) accepts, `r` (or Escape) rejects, and the model is told
which. An accepted edit goes into the file as one edit (Ctrl+Z in the
file takes it back) and is saved; View > Undo AI Changes puts back every
file it changed since your last question. A command it wants to run is
asked in the status bar (y / n); its output goes back to it. (The ide
waits while the command runs — keep those short.) It may keep notes about
the project in `.ide/memory.md`, read with the instructions every time.

`@terminal`, `@git`, `@file`, `@folder` or `@some/path` in a question
attaches more of that. Enter asks — while the AI is working (● working,
at the right of the input line) it queues the question, up to 10, each
asked when the one before is answered; an eleventh stays in the box.
Alt+Enter is a new line, ←/→ Home/End move the cursor (↑/↓ too, between
the lines of a long question); on its first or last line ↑/↓ bring
back the questions asked before. PgUp/PgDn
scroll (Ctrl+↑/↓ a line at a time), Ctrl+C stops the answer (and puts
the queued questions back in the box), Escape gives the keys back to the files,
Ctrl+W closes the tab (the conversation stays for next time), View > New
AI Chat starts over. Ctrl+T in the chat opens another conversation in a
tab of its own (View > New AI Chat Tab); each goes on answering while
another has the keys. Ctrl+L works from a terminal too (so there it no
longer clears the shell's screen — `clear` does).

**The model is yours to choose**, in settings.json (Settings > AI Model…
writes the entries in for you):

```json
"ai.provider": "local",
"ai.providers": {
  "local": {
    "type": "openai-compatible",
    "endpoint": "http://localhost:8080",
    "model": "qwen2.5-coder-14b",
    "apiKeyEnv": "LOCALAI_API_KEY",
    "contextTokens": 32768
  }
}
```

**Picking the AI: Alt+M** (or Settings > AI: Switch Model…) shows every
AI, and the models and efforts of the one under the cursor, side by side —
all the choices at once, ● on what is in use:

```
 AI                     │ Model            │ Effort
   local                │   (its default)  │   (default)
 ● Claude Code · claude │ ● Opus 5.5       │   low
   Codex · codex        │   Opus 5         │   medium
                        │   Sonnet 5       │ ● high
 Claude Code: ready
```

←/→ (or Tab) move between the lists, ↑/↓ within one, Enter picks, Escape
closes. Moving in the AI list shows that AI's models and efforts without
switching to it; picking one of them does. Each AI is checked as the lists
open — ready, not installed, not signed in, not reachable, the key refused
— and keeps its own model and effort. The status bar shows what is in use
(`Claude Code · Opus 5.5 · high · Ask`).

Nothing here is built into the ide. The models and efforts are the ones a
tool reports itself — a server's `/v1/models`; Codex's catalogue, with the
efforts each model takes and its default — or, where it cannot say, the
`"models"` / `"efforts"` lists in its entry, which win. A model there is a
name, or `{ "id": "claude-opus-5-5", "name": "Opus 5.5" }` — the id is what
the tool is given, the name what you see — so several versions of one
model can sit side by side. Claude Code's entry lists its models by their
versioned ids (Opus 5.5, Opus 5, Sonnet 5, Haiku 4.5, Fable 5.1, Fable 5 —
some need usage credits on some plans) and the efforts its `--effort`
takes; edit them there. Codex shows its own names for its models.
`local`, `claude` and `codex` are default entries of `ai.providers`, merged
under yours field by field (an entry giving only a `"model"` keeps the rest)
— add your own beside them. The local model takes no effort
yet (that needs the localai module to pass one on).

**Or Claude Code / Codex behind the same chat.** With `"ai.provider":
"claude"` or `"codex"` (or Alt+M) the chat runs
the `claude` or `codex` program you have installed and signed in to —
your own subscription, no API key, no per-question bill — out of sight,
and shows its steps and answers as they come; the ide keeps working
meanwhile. What you are looking at still goes with each question; they
read `CLAUDE.md` / `AGENTS.md` themselves, and the conversation carries
on until View > New AI Chat.

Alt+E (or Settings > AI: Ask ↔ Edit) switches the mode,
shown on the line over the input:

- **Ask** — it only reads (Claude in plan mode, Codex in a read-only
  sandbox).
- **Edit** — it changes files itself. After, the chat names what it
  changed; View > Show AI Changes (Ctrl+K D) opens each as a red / green
  diff, and View > Undo AI Changes puts them all back. That needs the
  folder to be a git repository (the ide takes a snapshot with `git stash
  create`, which touches nothing). Claude runs no commands but those in
  `"ai.agent.allowCommands"` (e.g. `["Bash(cargo test:*)"]`); Codex runs
  them inside its workspace sandbox.

```json
"ai.providers": {
  "claude": { "type": "claude-code", "command": "claude", "model": "",
              "models": [{ "id": "claude-opus-5-5", "name": "Opus 5.5" }, { "id": "claude-sonnet-5", "name": "Sonnet 5" }, "…"],
              "effort": "", "efforts": ["low", "medium", "high", "xhigh", "max"] },
  "codex":  { "type": "codex", "command": "codex", "model": "", "effort": "" }
},
"ai.agent.mode": "ask",
"ai.agent.planFollowup": "edit",
"ai.agent.allowCommands": []
```

Out of the box `local` is LocalAI at `http://localhost:8080`, its key
read from `LOCALAI_API_KEY` (unset, none is sent); name its model in
`model`, or pick one with Alt+M. `openai-compatible` is anything that
serves `/v1/chat/completions` — LocalAI, Ollama (`http://localhost:11434`), llama.cpp's server, vLLM, LM
Studio. A key never goes in the file: `apiKeyEnv` names the environment
variable that holds it. `contextTokens` is how much the model can take;
everything sent is cut to fit it. Other kinds of providers (Anthropic,
OpenAI's own) will be more `type`s, next to this one
([src/llm.gene.code](src/llm.gene.code)).

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
| Ctrl+K Ctrl+O | Open Folder… |
| Ctrl+S / Ctrl+W / Ctrl+Q | Save / close the tab / Exit (each asks first if unsaved) |
| Alt+← / Alt+→ | Go Back / Go Forward: where the cursor has been — another file, or a jump of 10 lines or more (View menu too) |
| Ctrl+Tab / Shift+Tab | Next / previous tab, round and round — GNOME's terminals send Ctrl+Tab as a plain Tab, so there only Shift+Tab arrives. In a terminal tab Shift+Tab is the shell's |
| Ctrl+\\ | Split Editor: the file again, in a second editor on the right |
| Ctrl+B / Ctrl+J / Ctrl+L / Ctrl+E | The Explorer / the terminal / the AI chat / the files: open and focus; focus; put away (see Pane keys) |
| Ctrl+0 / Ctrl+1 / Ctrl+2 | Focus the Explorer / the first / the second editor |
| F6 | Explorer, then each editor, round again |
| Alt+F Alt+V Alt+S Alt+H, F10 | Menus: arrows, Enter, Escape |
| Ctrl+Z / Ctrl+Y | Undo / redo (typing is one step per run) |
| Ctrl+K Ctrl+S | Keyboard shortcuts |
| Ctrl+, | Settings (settings.json) |
| Ctrl+K and an arrow | Move the focused side's edge (the left grows with →, the bottom with ↑) |
| Ctrl+K M | Move the tab to another place |
| Ctrl+K T | A new terminal |
| Ctrl+T | Another of what has the keys: a terminal in a terminal, an AI chat in the chat |
| Ctrl+Shift+N | New Window: another ide on this folder |
| Alt+M | The AI, its model and its effort |

In the editor: arrows, Home (first non-space, then column 0), End,
PageUp/PageDown, Ctrl+Home/End, Ctrl+Left/Right by word; Tab indents by
four spaces and Ctrl+K Shift+Tab takes a level back (code refuses tabs); Enter keeps the indentation and
adds a level after a block header (`… =>`, `if …`, `loop …` without a
comma). Ctrl+1 needs a terminal that tells it apart from 1 (kitty, foot, WezTerm,
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
  "ai.provider": "local",
  "ai.providers": { "local": { "type": "openai-compatible", "endpoint": "http://localhost:8080", "…": "" } },
  "ai.chat.location": "r",
  "ai.maxSteps": 12,
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
| `tabs` | what is open where: groups in slots, their tabs (files, the explorer, terminals, the chat) |
| `chatbox` | the AI chat's input box, the model's replies read, text wrapped |
| `context` | what the model is told: what is on screen, the instructions, the project map, the tools |
| `llm` | which model, from settings: provider types and the particles each takes |
| `agents` | Claude Code and Codex: the command that runs each, and their events read into the chat |

Everything but `ide` is pure: a particle in, a particle out. State lives in
one gene because a gene's top level is its handlers' whole world. A handler
that fails puts `Error: …` in the status bar instead of stalling.

Organelles: `tty` (keys in, a screen out — only changed rows are written),
`syntax` (spans from code's lexer, still coloured while a file does not
lex), `fs` (twice: the open folder, and the settings folder), `json`,
`strings`, `env`, `pty` (the terminals), `localai` (the model, over
`/v1/chat/completions`), `process` (ripgrep and git for the chat),
`http_client` (a model server's list of models).

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
launcher](bin/ide), and the ten organelles beside it. It needs no `code`
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
edited, undone, saved, the menu, the prompts, a frame drawn, and the AI
chat asked, stepping through a tool to its answer, its changes rejected,
accepted and undone, a command run — against a port that
never answers, so the replies the test hands in are the only ones),
[tests/chat.code](tests/chat.code) (replies read, the input box, wrapping,
the project map, providers from settings),
[tests/agents.code](tests/agents.code) (Claude Code's and Codex's events,
recorded from real runs in tests/fixtures, and the ide running
[a stand-in agent](tests/fake-agent.sh): asked, continued, editing, its
changes shown and undone, a missing program, stopped), all without a
terminal.

In a real terminal: `python3 tools/smoke.py` (from a checkout) or
`python3 tools/smoke.py <bundle>/ide` — a pty, keys pressed, the screen read
back by [tools/drive.py](tools/drive.py), a small emulator for what `tty`
sends (no tmux or pyte needed).

## Next

AI answers that appear as they are written, a meaning-based search index,
suggestions as you type, remote providers. And Ctrl+P, find, the
clipboard, the mouse, diagnostics from the language server, extensions.
