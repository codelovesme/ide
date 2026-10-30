# 004 — Speak to the AI chat: Ctrl+Shift+Space

The AI chat could only be typed into. One key turns the microphone on, the
same key turns it off, and what was said lands in the chat's input box —
not sent, so it can be read and fixed first; Enter sends it to whichever AI
is chosen (Claude Code, Codex, Mike, local).

Nobody is made to sign up for anything to use it. Claude Code's and
Codex's own voice features cannot be used from here: both live inside
their own interactive screens (Claude's `/voice`, Codex's TUI voice) and
their editor extensions talk to private endpoints with the subscription's
token (Claude: `wss://api.anthropic.com/api/ws/speech_to_text/voice_stream`;
Codex: the ChatGPT backend's `/transcribe`) — neither CLI offers "this
audio as text". Run inside an IDE terminal tab, they keep their own voice.

So what turns the recording into words is chosen in settings
(`ai.voice.provider`):

- `offline` — whisper.cpp's `whisper-cli`, shipped beside the ide, on this
  computer; nothing leaves it. The model (ggml-base, 142 MB) is downloaded
  once, after asking, sha256-checked, into `~/.cache/codelovesme-ide/models`.
- `openai-compatible` — any `/v1/audio/transcriptions`: OpenAI with your
  key, LocalAI, a whisper server (`ai.voice.endpoint`, `.model`,
  `.apiKeyEnv`; the key never in a file or a command line).
- `mike` — through the shared Mike service (`/v1/chat/hear`) to Mike's
  `Hear`; needs the IDE signed in to codelovesme.
- `auto` (the default) — Mike when signed in, else the endpoint when one is
  set, else offline.

Measured on the owner's machine (i7-5930K, CPU only, the 11 s JFK sample):
ggml-base 2.3 s, ggml-small 7.6 s — base is the default, small a setting.

Acceptance criteria:

- [x] Ctrl+Shift+Space (command `ai.voice`, View > Voice Input) starts the
      recorder in a hidden terminal; the status bar shows that it records
      and the chat's input line shows `● rec`; the ide keeps working.
- [x] The same key again stops it (Ctrl+C to the recorder, the WAV closed
      whole); Escape, or `ai.voice.cancel`, throws the recording away.
- [x] The recording is turned into text by the provider `auto` picks
      (signed in → mike; an endpoint → openai-compatible; else offline), or
      the one named; the words go into the chat box at the cursor, the chat
      is shown and focused, nothing is sent.
- [x] Offline without the model: a y / n prompt offers the download; y
      fetches it in a hidden terminal and checks its sha256; a bad file is
      not kept.
- [x] openai-compatible: the key reaches curl on stdin, never in argv;
      `apiKeyEnv` must be a variable name.
- [x] mike: the bridge (`mike_bridge.py --hear`) checks the IDE account
      against the service like a question does; the service's new
      `/v1/chat/hear` refuses when signed out, an empty or oversized
      recording, an unknown format; its body limit fits 60 s of audio.
- [x] A failure (no recorder, no whisper-cli, server refused, nothing
      heard) is said in the status bar; the ide never waits on it.
- [x] The key works from a terminal tab too (a pane command, like Ctrl+L), and
      arrives in cdlvsm-console as `ctrl+shift+space` (kitty protocol).
- [x] The release bundle carries `whisper-cli` (built from whisper.cpp,
      pinned) and the smoke test checks it is there and runs.
- [x] `euglena test` (code v2.14.5), `tools/test_mike_bridge.py`, and the
      mike service's tests stay green with new cases for all of the above.

Verified 2026-10-30 (pinned toolchain: code v2.14.5, euglena v0.4.3):

- `code test`: all 10 fixture files pass; the new tests/voice.code drives
  the ide with a stand-in recorder and whisper-cli through record → stop →
  heard → box, again at the cursor, Escape, the model offer (n), a missing
  recorder, ● REC in a frame; the lines (no key on a command line, a bad
  `apiKeyEnv` refused), the answers, settings fallbacks, the key binding.
- `tools/test_mike_bridge.py`: 14 pass (new: hear as base64 WAV, another
  account / signed-out IDE refused, an old service and a long recording
  say why). mike-desktop `service/` tests: 7 pass (new: hear signed out
  409, empty 400, unknown format 400, Mike could not make it out 503, the
  `Hear` particle sent with the account's token).
- The packaged bundle (`tools/package.sh`, whisper-cli built by
  tools/whisper.sh: libc/libm only, 4.9 MB) under `tools/smoke.py`: 54
  checks pass, among them ctrl+shift+space sent as kitty's `ESC[32;6u`
  recording, the same key stopping it, the words in the box, and the
  bundle's whisper-cli running. (The View-menu walk to Move Tab is one
  step longer for the new item.)
- End to end in the packaged ide, real parts: offline — the y/n offer, the
  real 142 MB download in 5.5 s, sha256 checked, no .part left, the real
  whisper-cli hearing the JFK sample in 2.5 s into the box;
  openai-compatible — LocalAI's whisper-large with the real key from
  `LOCALAI_API_KEY`, 0.6 s; the real pw-record (a monitor source) started
  and stopped by the key, its WAV closed whole and heard. A wrong sha256
  leaves no model behind.
- Measured: ggml-base 2.3–2.6 s, ggml-small 7.6 s for the 11 s sample on an
  i7-5930K (CPU) — base is the default.

Not verified live: the Mike path end to end — this IDE is not signed in to
codelovesme, and the shared service on this computer is the released 0.5.0
without `/v1/chat/hear` (it says "too old to hear" until it is upgraded).
Whisper invents a short phrase ("Thank you.") for a silent recording;
since nothing is sent before Enter, it is seen and cleared.
