# 006 — Ctrl+P, Ctrl+F and the clipboard in the editor

The editor had no way to open a file by name, find text in a file, or
copy and paste — the selection was kept (Shift+arrows, Ctrl+A) but not
shown, and `CopyText` / `PasteText` were wired to no key. VS Code's keys,
not the AI's (those start with Ctrl+Shift).

Acceptance criteria:

- [x] Ctrl+P (Go to File…) asks for a name: as it is typed, the project's
      files that match are listed (the name's own letters first, then
      anywhere in the path; ignored files left out, as `rg --files` /
      `git ls-files` do); ↑/↓ pick one, Enter opens it, Escape closes.
- [x] Ctrl+F (Find) in a file: as it is typed, the cursor goes to the
      next match from where it was (case-insensitive) and the match is
      selected; Enter goes to the next one, round past the end; the status
      bar says how many there are ("2 of 5"), or that there are none;
      Escape closes the box, the cursor and the selection where they are.
- [x] The selection is drawn in the editor (a lit background), so what
      Shift+arrows, Ctrl+A and Find selected can be seen.
- [x] In a file, Ctrl+C copies the selection, Ctrl+X cuts it (one undo
      step), Ctrl+V pastes over it at the cursor, line breaks kept (one
      undo step) — through the desktop's clipboard, the ide's own when
      there is none. Nothing selected: Ctrl+C / Ctrl+X say so.
- [x] In the AI chat's box Ctrl+V pastes too; Ctrl+C there still stops
      the answer. In a terminal Ctrl+C / Ctrl+V / Ctrl+P / Ctrl+F stay the
      shell's.
- [x] Ctrl+K Ctrl+S, the README's key table and the menus list the new
      keys.
- [x] Every current test still passes (`code test`, 10 files).
- [x] Seen working in a real terminal (tools/drive.py): Ctrl+P opens a
      file, Ctrl+F finds, copy and paste a line.

Verified: `code test` 10/10 (tests/ide.code: Ctrl+P matches and order,
Find counts / next / previous / round / none, the selection drawn,
copy / cut / paste with undo, Ctrl+V in the chat); in a real pty
(tools/smoke.py with the pinned `code run`): Ctrl+P lists, Ctrl+F counts,
copy and paste a line — with no desktop session, so through the ide's own
clipboard. The strings organelle in use has no IndexOf / Contains, so the
search is done in the gene (`IndexIn`, editor.gene.code).
