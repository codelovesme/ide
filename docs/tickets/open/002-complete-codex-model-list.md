# 002 — Show the complete Codex model catalogue

The model picker currently removes every Codex catalogue entry whose
`visibility` is `hide`. That makes the list look hard-coded or incomplete even
though it comes from `codex debug models`.

Acceptance criteria:

- [x] The Codex picker includes every model returned by `codex debug models`,
      including entries marked hidden.
- [x] A hidden Codex entry is visibly labelled `(hidden)` in the model list.
- [x] The model id, display name, supported efforts, and default effort still
      come from the Codex catalogue.
- [x] Configured model lists and OpenAI-compatible `/v1/models` discovery keep
      their existing behaviour.
- [x] `euglena test` passes, including a deterministic complete-catalogue
      regression case.
- [x] The built IDE shows the complete live Codex catalogue in its model
      picker.

Verified 2026-09-26: `euglena test` passed 7/7 fixtures; the terminal smoke
test passed every check against the built application; the live Codex command
returned 7 entries (5 listed and 2 hidden), all of which now enter the picker.
