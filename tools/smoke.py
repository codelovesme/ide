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
s = Session(argv, cwd, {"IDE_FOLDER": folder, "TERM": "xterm-256color", "XDG_CONFIG_HOME": config})
failures = []
def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)

check(s.wait_for("EXPLORER", 30), "starts, with the explorer")
check(s.screen.row(0).startswith("  File  View  Help"), "menu bar on row 0")
check(s.screen.row(2).rstrip() == " ▸ src", "tree fills the screen: " + s.screen.row(2).rstrip())
s.keys(b"\r")
s.keys(b"\x1b[B\r", 1.0)
check("hello.code" in s.screen.row(1), "file opens beside the tree")
check(s.screen.row(2)[30:].startswith("   1 | hi"), "line numbers and text: " + s.screen.row(2)[30:50])
check((78, 201, 176) in s.screen.fgs[3], "code is coloured (Greet as a class)")
s.keys(b"yo ", 0.8)
check("●" in s.screen.row(1), "typing marks the file dirty")
s.keys(b"\x13", 0.8)
check(open(folder + "/src/hello.code").read().startswith("yo | hi"), "ctrl+s saves")
s.keys(b"\x05", 0.6)
s.keys(b"\x1b[B\r", 1.0)
check("notes.md" in s.screen.row(1), "ctrl+e (ctrl+shift+e in most terminals) goes to the explorer; down, enter opens the next file")
s.keys(b"\x1bf", 0.6)
check("Open Folder" in s.screen.row(1), "alt+f opens the File menu")
s.keys(b"\x1b", 0.6)
s.keys(b"\x02", 0.6)
check("EXPLORER" not in s.screen.row(1), "ctrl+b hides the explorer")
s.keys(b"\x02", 0.6)
s.keys(b"\x0b\x1b[C", 0.8)
check(s.screen.row(1)[32:].startswith(" notes.md"), "ctrl+k → makes the explorer wider: " + s.screen.row(1)[28:44])
settings = open(config + "/codelovesme-ide/settings.json").read()
check('"workbench.sideBar.width": 32' in settings, "and settings.json remembers it")
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
