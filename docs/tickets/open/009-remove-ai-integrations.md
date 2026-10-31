# 009 — No AI inside the ide

The owner (2026-10-31): "Remove the Claude and Codex integrations. The IDE
will have no AI integration at all — Mike and the local model too." Claude
Code, Codex and the rest run in the ide's own terminal tab, so the ide
needs no separate integration. The reason: each time their CLIs change,
the ide has to change with them; that dependency goes.

What goes:

- The AI chat: `src/chatbox`, `context`, `llm`, `agents` genes; the `chat`
  and `diff` tab kinds; chat tabs (`chats`, `chat_id`, ChatOwner/InChat);
  Show AI Changes / Undo AI turn; plan follow-up (Alt+G).
- The providers: Claude Code, Codex (incl. the CLI update check and model
  lists), the local model (the `localai` organelle in manifest.json and
  .code/lock.json).
- Mike: Settings > Account sign-in, `tools/mike_bridge.py`,
  `tools/mike-e2e.py`, `tools/mike-login-e2e.py`, `tools/browser-login.mjs`,
  `tools/test_mike_bridge.py`, `docs/mike.md`, the `feature.mike` line and
  the bridge copy in `tools/package.sh`.
- Voice input (it only fed the chat): `src/voice`, `tools/whisper.sh`,
  whisper-cli in the bundle.
- Their keys, menu items and settings: Ctrl+L, Ctrl+Shift+M, Shift+Tab mode
  switch, Ctrl+K D, Ctrl+Shift+Space, View > AI Chat / New AI Chat Tab /
  Voice Input, every `ai.*` setting (an old settings.json carrying them
  still loads).
- Their tests and fakes: `tests/agents`, `chat`, `voice`, `mike`,
  `account`, `tests/fixtures/*.jsonl`, `fake-agent.sh`, `fake-mike.py`,
  `fake-recorder.sh`, `fake-whisper.sh`; the AI parts of tools/smoke.py.
- README's AI chat, voice and Mike sections. Ticket 005 (Codex realtime
  voice) is dropped with it.

What stays: the editor, explorer, tabs, groups, terminal tabs (Ctrl+T
opens a terminal), New Window, settings.json, keybindings.json, the mouse
and every editor key.

Acceptance criteria:

- [ ] None of the above is in the repo (`grep -ri -E
      "claude|codex|mike|localai|whisper|voice|ai\.chat"` over src, tests,
      tools, README finds nothing but this ticket's history).
- [ ] The ide starts, opens files, edits, saves, opens a terminal tab, and
      `claude` / `codex` run in it as in any terminal.
- [ ] A settings.json or keybindings.json with the old `ai.*` entries and
      AI commands opens without error.
- [ ] The Release workflow's trial run (tests + smoke) is green; the bundle
      has no whisper-cli or mike_bridge.py and is smaller.
- [ ] Released as a minor version and installed with `cdlvsm install ide`.

Outside this repo: cdlvsm's `install ide --with mike` and the
`feature.mike` package line — cdlvsm should stop offering it (a separate
change in cdlvsm).
