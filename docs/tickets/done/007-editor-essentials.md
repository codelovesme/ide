# 007 — What a text editor is expected to do

The owner: "all of them" — the features every editor has, kept in the
pure editor gene (editor.gene.code) so the console can use the same one
later. Keys follow the owner's rules: AI keys are Ctrl+Shift, Alt is for
menus — Alt+↑/↓ (move line) is the one exception they approved. No
delete-line key: select (Shift+End / Shift+↓) and Delete.

Acceptance criteria:

- [x] Ctrl+Backspace / Ctrl+Delete delete a word back / forward (at a line's
      edge they join lines, as Backspace / Delete do).
- [x] Ctrl+D: nothing selected — the word at the cursor is selected; again —
      the next same text is selected too, with a cursor of its own
      (multi-cursor), round past the end.
- [x] With several cursors, typing, Enter, Backspace, Delete, Tab, the word
      keys and the moves (with Shift too) act at every one; Escape leaves
      only the first. Each extra cursor and its selection are drawn.
- [x] Alt+↑ / Alt+↓ move the line, or the selected lines, up / down.
- [x] Ctrl+/ comments the line or the selected lines out — or in, when all
      are comments — with the language's mark (`|` code, `#` shell / python
      / yaml / toml, `//` js / ts / rust / go / c / java …).
- [x] Ctrl+H: find, then the text to put instead; Enter replaces every one
      (case left aside, as Find), one undo step, and says how many.
- [x] Ctrl+G: go to a line (`12`, or `12:5` for a column too).
- [x] Brackets and quotes close themselves: `(` gives `()` with the cursor
      inside; typing the closer steps over it; Backspace between an empty
      pair takes both; with a selection, it is wrapped.
- [x] The bracket that matches the one at the cursor is lit, both lit.
- [x] Word wrap (View > Word Wrap, `editor.wordWrap`: "on" / "off"): long
      lines go on in the rows below instead of off the side.
- [x] Ctrl+K Ctrl+S, the README and the menus list them.
- [x] Every current test still passes (`code test`), and tools/smoke.py
      (apart from the bundle-only whisper check).
- [x] Seen working in a real terminal (tools/drive.py).

Not here: the mouse — the tty module drops mouse reports, so it needs a
change to `code` (asked separately).

Verified: `code test` 10/10 (tests/editor.code: word delete, move lines,
comments, pairs, Ctrl+D and every cursor; tests/ide.code: Ctrl+G, Ctrl+H,
two cursors drawn and undone, the bracket pair lit, word wrap on / off);
tools/smoke.py green but the bundle-only whisper check; a real pty: Ctrl+D
twice and typing at both, Alt+↓, Ctrl+/, Ctrl+G 3:14, Ctrl+Backspace, `(`.
