# 003 — Tell the user when an agent CLI has an update

The IDE runs installed coding-agent CLIs such as Codex and Claude Code. It
should check their installed versions against the latest published package
versions and tell the user when an update is available. It must not install or
update anything.

Acceptance criteria:

- [x] On IDE startup, check each configured CLI provider that supplies update
      metadata; skip providers that are not installed.
- [x] When one CLI has an update, show its name and both versions in the
      status bar; when several do, point to Alt+M and show each version there.
- [x] A failed CLI or network check leaves the IDE usable and does not show a
      false update notice.
- [x] The version source and command can be configured per CLI provider type,
      so another agent CLI can be added later.
- [x] No command is run to install or update a CLI.

Verified 2026-09-26:

- `cdlvsm euglena test`: all 7 fixture files passed. The chat fixture checks
  that LocalAI is an API provider with no CLI update source, version metadata
  for Codex and Claude Code, and version comparisons.
- `cdlvsm euglena build --target shared`: passed; the terminal smoke check
  passed all cases.
- In a temporary config with LocalAI selected, the IDE showed LocalAI ready
  and its model, displayed the exact Codex installed/latest version notice,
  and returned `LOCALAI_OK` from a chat prompt.
- With configured Codex and Claude commands missing, the IDE still opened and
  showed no false update notice.
