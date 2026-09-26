# 001 — Codex auto-approval when resuming a session

The IDE's `auto` mode must use the approval option supported by each Codex
command shape. `codex exec` accepts `--approve-for-me`, while its `resume`
subcommand accepts the equivalent `approvals_reviewer = "auto_review"`
configuration instead.

Acceptance criteria:

- [x] A new Codex session in `auto` mode still emits `--approve-for-me`.
- [x] A resumed Codex session in `auto` mode emits
      `approvals_reviewer="auto_review"` and does not emit
      `--approve-for-me` after `resume`.
- [x] Ask and edit command generation remains unchanged.
- [x] `euglena test` passes, including the agent regression case.

Verified 2026-09-26: `cdlvsm euglena test` passed all 7 test files, including
the Codex resume approval regression case. The implementation and regression
assertion are in commit `a1ff973`.
