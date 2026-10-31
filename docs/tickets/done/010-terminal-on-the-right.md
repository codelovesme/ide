# 010 — The terminal opens on the right, where the AI chat was

The owner (2026-10-31): with the AI chat gone (009), the right side is
empty. The terminal goes there instead of the bottom, the way the chat
sat, so the code gets the full height and the bottom stays empty.
`claude`, `codex` and `mike-cli` (mike-desktop 005) then run on the right,
where the chat used to be.

Today: `ToggleTerminal` opens the first terminal with `NewTerminal { slot =
"b" }`, and `NewTerminal` with an empty slot falls back to `"b"`
(src/ide.gene.code ~786–812); README says "opens one at the bottom".

Acceptance criteria:

- [x] Ctrl+J / Ctrl+\` / View > Terminal with no terminal open opens it on
      the right (slot `r`), full height beside the editor; the bottom row
      is not there (empty tracks collapse, as today).
- [x] View > New Terminal (Ctrl+K T) with no terminal focused also goes to
      the right; from a focused terminal it still opens beside that one.
- [x] A setting `terminal.location` (l r t b c tl tr bl br, default `r`)
      picks the place, checked like `ai.chat.location` was; a wrong value
      is reported and the default used.
- [x] Moving a terminal tab elsewhere (Move Tab) still works, and an
      already-open terminal is not moved by this change.
- [x] Its width: the right column's width as the chat had it (40),
      resizable with Ctrl+K and an arrow; the pty is resized to fit.
- [x] `code test` green (tests/ide.code / layout.code assert slot `r`);
      tools/smoke.py opens a terminal and sees it on the right; README's
      terminal section updated.
- [x] Released with 009 (or after it) as a minor version and installed.

Done (2026-10-31, with 009): `terminal.location` (default `r`) in
settings.gene.code; NewTerminal, Ctrl+J/Ctrl+\` and Ctrl+T use it; Move Tab
on a terminal stores the new place. tests/ide.code checks the default and
the right-hand terminal, tools/smoke.py that it opens on the right, full
height, and that a move to the bottom is remembered.
