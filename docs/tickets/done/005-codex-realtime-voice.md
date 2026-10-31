# 005 — Talk with Codex: its realtime voice through `codex app-server`

Dropped (2026-10-31): the ide has no AI integration any more (009);
Codex's own voice works in a terminal tab.

Voice input (004) turns speech into text and leaves the sending to Enter.
Codex offers more, with the user's own Codex/ChatGPT sign-in and no
codelovesme account: `codex app-server` (the JSON-RPC protocol its VS Code,
JetBrains and Zed integrations use; `codex app-server generate-json-schema`
publishes it) has `thread/realtime/start | appendAudio | appendText | stop`
and the events `thread/realtime/item/transcript/delta|done`,
`thread/realtime/outputAudio/delta`, `thread/realtime/error|closed`.

It is a spoken conversation, not dictation: the model may answer aloud.
It is marked experimental, and the ide today runs Codex as
`codex exec --json` (src/agents.gene.code), not app-server — so this
starts with moving the Codex provider onto app-server.

Claude Code has no counterpart: its `/voice` lives in its own screen, and
its extension talks to a private endpoint with the subscription token.

Acceptance criteria:

- [ ] The Codex provider runs on `codex app-server` (stdio JSON-RPC) with
      everything `codex exec` gives today: ask/plan/edit/auto, resume, the
      model and effort, its steps in the chat, Ctrl+C stopping a turn —
      every current agents fixture still passes.
- [ ] With Codex chosen, a setting (`ai.voice.codexRealtime`) makes
      Ctrl+Shift+Space start a realtime session on the chat's thread,
      stream the microphone (16 kHz PCM) as `appendAudio`, and show the
      user's transcript and Codex's reply as they arrive.
- [ ] Codex's spoken reply is played (`outputAudio`), and can be muted.
- [ ] The same key, or Escape, ends the session (`thread/realtime/stop`);
      an error or a closed session is said in the status bar.
- [ ] Not signed in to Codex, or a Codex without realtime: says so and
      falls back to 004's voice input.
- [ ] Verified live with the installed `codex` and the owner's microphone;
      the protocol pinned to a recorded fixture of a real session.
