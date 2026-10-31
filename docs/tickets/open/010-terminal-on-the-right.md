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

- [ ] Ctrl+J / Ctrl+\` / View > Terminal with no terminal open opens it on
      the right (slot `r`), full height beside the editor; the bottom row
      is not there (empty tracks collapse, as today).
- [ ] View > New Terminal (Ctrl+K T) with no terminal focused also goes to
      the right; from a focused terminal it still opens beside that one.
- [ ] A setting `terminal.location` (l r t b c tl tr bl br, default `r`)
      picks the place, checked like `ai.chat.location` was; a wrong value
      is reported and the default used.
- [ ] Moving a terminal tab elsewhere (Move Tab) still works, and an
      already-open terminal is not moved by this change.
- [ ] Its width: the right column's width as the chat had it, resizable
      with the existing pane keys; the pty is resized to fit.
- [ ] `code test` green (tests/ide.code / layout.code assert slot `r`);
      tools/smoke.py opens a terminal and sees it on the right; README's
      terminal section updated.
- [ ] Released with 009 (or after it) as a minor version and installed.
