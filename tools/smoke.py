"""The ide in a real terminal: a pty, the keys a person presses, the
screen read back. No tmux or pyte needed — drive.py is a small emulator
for exactly what the tty module sends.

    python3 tools/smoke.py                 # from a checkout: cdlvsm euglena run
    python3 tools/smoke.py <bundle>/ide    # a packaged or installed ide

Exits non-zero, saying what, if anything is not as it should be.
"""
import os, shutil, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drive import Session

app = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
folder = tempfile.mkdtemp(prefix="ide-smoke-")
os.makedirs(folder + "/src")
open(folder + "/src/hello.code", "w").write("| hi\nGreet { who } =>\n    return Hi\n")
open(folder + "/notes.md", "w").write("notes\n")

if len(sys.argv) > 1:
    argv, cwd = [os.path.abspath(sys.argv[1])], folder
else:
    cdlvsm = shutil.which("cdlvsm")
    if not cdlvsm:
        sys.exit("needs cdlvsm on PATH (with euglena installed), or a path to the ide to run")
    argv, cwd = [cdlvsm, "euglena", "run"], app
config = tempfile.mkdtemp(prefix="ide-smoke-config-")
os.makedirs(config + "/codelovesme-ide")
open(config + "/codelovesme-ide/keybindings.json", "w").write('[ { "key": "ctrl+g", "command": "view.explorer" } ]\n')
# The local model has no endpoint; "fake" stands in for Claude Code.
open(config + "/codelovesme-ide/settings.json", "w").write('{ "ai.providers": { "local": { "type": "openai-compatible", "endpoint": "" }, "fake": { "type": "claude-code", "command": "%s/tests/fake-agent.sh" } } }\n' % app)
s = Session(argv, cwd, {"IDE_FOLDER": folder, "TERM": "xterm-256color", "XDG_CONFIG_HOME": config})
failures = []
def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)

check(s.wait_for("Explorer", 30), "starts, with the explorer")
check(s.screen.row(0).startswith("  File  View  Settings  Help"), "menu bar on row 0")
check(s.screen.row(1).startswith(" Explorer ") and s.screen.row(3).rstrip() == " ▸ src", "the explorer is a tab, and fills the screen: " + s.screen.row(3).rstrip())
s.keys(b"\x07", 0.6)
check(" Explorer " not in s.screen.row(1), "a key from keybindings.json runs its command (ctrl+g hides the explorer)")
s.keys(b"\x07", 0.6)
s.keys(b"\r")
s.keys(b"\x1b[B\r", 1.0)
check("hello.code" in s.screen.row(1), "file opens beside the tree")
check(s.screen.row(2)[31:].startswith("   1 | hi"), "line numbers and text: " + s.screen.row(2)[31:50])
check((78, 201, 176) in s.screen.fgs[3], "code is coloured (Greet as a class)")
s.keys(b"yo ", 0.8)
check("●" in s.screen.row(1), "typing marks the file dirty")
s.keys(b"\x13", 0.8)
check(open(folder + "/src/hello.code").read().startswith("yo | hi"), "ctrl+s saves")
s.keys(b"\x02", 0.6)                        # ctrl+b: the explorer is shown — the keys to it
s.keys(b"\x1b[B\r", 1.0)
check("notes.md" in s.screen.row(1), "ctrl+b goes to the explorer; down, enter opens the next file")
check(s.screen.row(1)[31:].startswith(" hello.code  notes.md "), "each open file has a tab: " + s.screen.row(1)[31:56])
s.keys(b"\x1b[9;5u", 0.8)
check(s.screen.row(0).rstrip().endswith("src/hello.code"), "ctrl+tab (as terminals that tell it apart send it) goes to the next tab")
s.keys(b"\x1b[9;5u", 0.8)
check(s.screen.row(0).rstrip().endswith("notes.md"), "ctrl+tab again goes round, past the last tab to the first")
s.keys(b"\x1b[1;3D", 0.8)                  # alt+left
check(s.screen.row(0).rstrip().endswith("src/hello.code"), "alt+← goes back to where the cursor was")
s.keys(b"\x1b[1;3C", 0.8)                  # alt+right
check(s.screen.row(0).rstrip().endswith("notes.md"), "alt+→ goes forward again")
s.keys(b"\x1c", 0.8)
check(s.screen.row(1).count("notes.md") == 2 and "│" in s.screen.row(2), "ctrl+\\ splits: the file again, in a second editor on the right")
s.keys(b"\x17", 0.8)
check(s.screen.row(1).count("notes.md") == 1, "ctrl+w closes it again")
s.keys(b"\x1bf", 0.6)
check("New File" in s.screen.row(1) and "Ctrl+N" in s.screen.row(1) and "Ctrl+K Ctrl+O" in s.screen.row(2), "alt+f opens the File menu, with each item's key")
s.keys(b"\x1b", 0.6)
s.keys(b"\x1bs", 0.6)
check("Settings (JSON)" in s.screen.row(1) and "Ctrl+," in s.screen.row(1) and "Keyboard Shortcuts (JSON)" in s.screen.row(2), "alt+s opens the Settings menu")
s.keys(b"\x1b", 0.6)
s.keys(b"\x02\x02", 0.8)                    # ctrl+b: the keys to it; again: put away
check("Explorer" not in s.screen.row(1), "ctrl+b twice puts the explorer away")
s.keys(b"\x02", 0.6)                        # and back, with the keys
s.keys(b"\x0b\x1b[C", 0.8)
check(s.screen.row(1)[33:].startswith(" hello.code "), "ctrl+k → makes the explorer wider: " + s.screen.row(1)[28:44])
settings = open(config + "/codelovesme-ide/settings.json").read()
check('"workbench.layout.left": 32' in settings, "and settings.json remembers it")
s.keys(b"\x1b[H", 0.6)                     # in the explorer: its first row (src)
s.keys(b"\x0e", 0.6)                       # ctrl+n
check("New file in src/:" in s.screen.row(39), "ctrl+n asks for a name, in the folder picked in the explorer")
s.keys(b"made.code\r", 1.0)
check(os.path.isfile(folder + "/src/made.code") and "made.code" in s.screen.row(1), "the file is made there and opened")

# The AI chat: Ctrl+L opens it on the right; with no model set up it says how.
s.keys(b"\x0c", 1.0)
right = "\n".join(s.screen.row(r)[60:] for r in range(1, 39))
check(" AI Chat " in right and "Ask about this project" in right, "ctrl+l opens the AI chat on the right")
check("No AI model is set up" in right, "with no model, the chat says how to set one up")
s.keys(b"hello", 0.6)
check(any("› hello" in s.screen.row(r) for r in range(30, 39)), "typing goes to the chat's input box")
s.keys(b"\x15\x1b", 0.8)                  # ctrl+u clears it; escape back to the files
s.keys(b"\x0c", 0.8)                      # ctrl+l again gives the chat the keys
s.keys(b"\x17", 0.8)                      # and ctrl+w closes its tab
check(not any(" AI Chat " in s.screen.row(r) for r in range(1, 39)), "ctrl+w closes the chat")

# An agent behind the chat (the stand-in for Claude Code): switched to from
# the Settings menu; the ide keeps answering keys while it works.
s.keys(b"\x1bm", 1.5)                      # alt+m: the AIs, models, efforts side by side
screen_text = s.screen.text()
check(" Model" in screen_text and " Effort" in screen_text and "● local" in screen_text and "Claude Code" in screen_text and "Codex" in screen_text, "alt+m shows every AI, and its models and efforts, at once")
check("local: not set up" in screen_text, "and how the AI under the cursor stands")
s.keys(b"\x1b[D\x1b[F\r", 1.0)            # ← to the AIs, End (the fake one), Enter
check("● Claude Code · fake" in s.screen.text(), "Enter picks an AI")
s.keys(b"\x1b", 0.8)
check("Claude Code · Ask" in s.screen.row(39), "the status bar shows the AI picked")
s.keys(b"\x0c", 0.8)
check(any("Claude Code · Ask" in s.screen.row(r) for r in range(1, 39)), "the chat names the agent and its mode")
s.keys(b"slow one\r", 1.5)
check(any("Claude Code is working" in s.screen.row(r) for r in range(1, 39)), "the agent works out of sight")
s.keys(b"abc", 0.8)
check(any("› abc" in s.screen.row(r) for r in range(1, 39)), "and the ide still takes keys meanwhile")
s.keys(b"\x03", 1.0)
check(any("Stopped." in s.screen.row(r) for r in range(1, 39)), "ctrl+c stops it")
s.keys(b"\x15what is it?\r", 0.5)
check(s.wait_for("It greets.", 10), "its steps and answer arrive in the chat")
s.keys(b"\x17", 0.8)

# The integrated terminal.
s.keys(b"\x00", 1.5)   # ctrl+` — what most terminals send for it
bottom = lambda: "\n".join(s.screen.row(r) for r in range(28, 39))
check(any(" Terminal 1 " in s.screen.row(r) for r in range(25, 30)), "ctrl+` opens a terminal at the bottom")
s.keys(b"echo hello-ide\r", 1.5)
check(s.wait_for("hello-ide\n", 5) or bottom().count("hello-ide") >= 2, "typing runs in the shell: echo hello-ide")
s.keys(b"printf '\\033[31mRED-TEXT\\033[0m\\n'\r", 1.5)
reds = [(r, c) for r in range(25, 39) for c in range(120) if s.screen.fgs[r][c] == (205, 49, 49)]
check(len(reds) >= 8, "the terminal's colours show (red text is red)")
s.keys(b"sleep 30\r", 0.8)
s.keys(b"\x03", 0.8)
s.keys(b"echo after-interrupt\r", 1.5)
check("after-interrupt" in bottom().replace("echo after-interrupt", ""), "ctrl+c reaches the shell")
s.keys(b"\x1bv", 0.6)                       # View menu (works from a terminal)
s.keys(b"\x1b[B" * 10 + b"\r", 0.6)         # Move Tab…
s.keys(b"r\r", 1.5)
right_half = "\n".join(s.screen.row(r)[60:] for r in range(1, 39))
check(" Terminal 1 " in right_half and "hello-ide" in right_half, "move tab: the terminal goes to the right, shell and all")
s.keys(b"seq 1 120\r", 1.2)
s.keys(b"\x1b[5;2~", 1.0)                   # shift+pageup
check(any("lines back" in s.screen.row(r) for r in range(1, 39)), "shift+pgup scrolls the terminal back")
s.keys(b"\x1b[6;2~" * 20, 1.0)              # shift+pagedown, back to the live screen
s.keys(b"\x00", 0.8)                        # ctrl+` with the terminal focused: put away
check(not any(" Terminal 1 " in s.screen.row(r) for r in range(1, 39)), "the terminal key puts a focused terminal away")
s.keys(b"\x00", 0.8)
check(any(" Terminal 1 " in s.screen.row(r) for r in range(1, 39)), "and brings it back, shell and all")
s.keys(b"\x05", 0.8)                        # ctrl+e: the keys to the files
s.resize(90, 20, 1.2)
check("Ln 1" in s.screen.row(19), "redraws at a new size")
s.keys(b"x\x11", 0.8)
check("Save changes" in s.screen.row(19), "ctrl+q with changes asks first")
s.keys(b"n", 1.5)
check(s.exit == 0, "exits cleanly")
check(not s.screen.alt and s.screen.visible, "terminal given back")
shutil.rmtree(folder)
shutil.rmtree(config)
sys.exit(1 if failures else 0)
