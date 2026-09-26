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
- [ ] `euglena test` passes, including the agent regression case.

Verification note: the new agent assertion passes in a clean worktree. The
full suite still has pre-existing failures in the Ctrl+C cleanup and chat
focus cases; the working checkout also contains unrelated editor changes
that currently prevent the suite from starting there.
