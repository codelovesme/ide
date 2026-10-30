# 008 — The mouse, and VS Code's copy-line / add-cursor keys

The owner: "yes" to the mouse (it needs a change to code's tty module),
and VS Code's keys for copying a line and adding a cursor above / below.

Acceptance criteria:

- [x] code's tty: `Start { mouse = "Mouse" }` asks the terminal for SGR
      mouse reports and pushes `Mouse { kind, button, row, col, shift, alt,
      ctrl, clicks }`; without `mouse` nothing changes; the terminal is
      given the mouse back at Stop (code branch `tty-mouse`, cargo tests).
- [x] A click puts the cursor there; a drag selects; a double click the
      word; a triple the line; Shift+click selects to it; Alt+click adds a
      cursor; the wheel scrolls three lines; a click on a tab shows it, in
      the explorer opens, on a menu title opens it, on an item runs it.
- [x] With an older tty the ide starts and works with keys as before.
- [x] Ctrl+Shift+Alt+↑/↓ copy the line(s) above / below; Shift+Alt+↑/↓
      add a cursor above / below. Ctrl+Shift+↑/↓ select (the owner's
      choice over VS Code's add-cursor), as Ctrl+Shift+←/→ do by word.
- [x] `code test` 10/10; tools/smoke.py as before; a real pty with the
      patched tty: click, drag, double click, wheel, menu by click, mouse
      given back on exit.

Left: a code release with the tty change, then the ide's lock moved to it
— until then the ide's bundle ships the old tty, so no mouse.
