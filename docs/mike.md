# Mike as an IDE provider

Alt+M → Mike, or `"ai.provider": "mike"` in settings. Claude Code, Codex
and OpenAI-compatible providers retain their existing paths. Mike does not
need a raw model URL and does not start a model, an agent CLI or another
machine executor. IDE talks to the user's existing shared Mike service.

The optional packaged dependency is `cdlvsm install ide --with mike`; it
resolves `mike-service`, not `mike-cli`. This describes package source support:
no new release assets have been published by this change. A staged IDE bundle
contains `mike_bridge.py`; the service dependency supplies its generic Python
local-protocol client. Python is supplied/checked by that dependency. In a
checkout the adapter also finds the adjacent `mike-desktop/client`; an explicit
`MIKE_SERVICE_CLIENT_DIR` selects a development service client.

## Signing in

Mike in IDE uses your codelovesme account. **Settings → Account: Sign In
(codelovesme)** opens the ordinary browser page (`/desktop/connect`, the
same handoff Mike Desktop and the desktop app windows use: one-use state,
the session in a loopback POST body, never in a URL). Sign in there and press
Connect. IDE plus the shared service is enough: no Mike Desktop or CLI, no
copied token, no environment token. If the service is not running, sign-in
(or a Mike question) starts the installed one — the user unit, else the
launcher CDLVSM resolved (`.cdlvsm-deps/mike-service`), a checkout's, or
`mike-service` on PATH; when none is installed IDE says so and starts nothing
else.

The session goes from the browser straight to the service's normal `attach`;
IDE keeps only the account name (`account.json` beside settings, 0600) and
never writes the token to settings, project files, run files, argv or logs.
Every Mike question checks that the service is connected as that same
account; otherwise it stops with the reason:

| State | What IDE says / does |
|---|---|
| never signed in, or signed out of IDE | sign in |
| browser closed / Account: Sign In again while waiting | sign-in cancelled, nothing changed (also after 5 min) |
| session refused or expired | sign in again; the same account refreshes the service's session |
| gateway unreachable | offline; IDE keeps its account, nothing is switched |
| service signed in to a different account | refused, never switched |
| service access revoked | sign in with Account: Switch Shared Mike Service |

**Account: Sign Out of IDE** is IDE-local: Mike chats end, the account record
is removed; the shared service, Desktop, CLI and other apps stay signed in.
**Account: Switch Shared Mike Service…** is the explicit choice to move this
computer's service to the account you sign in with (the service ends the old
account's generation for every client, as Desktop's Connect does). A sign-in
or account change closes running Mike chats; the transport also stops a turn
whose service or IDE account changes. Signing in grants no local tool
permissions and is not headless device enrollment. Open files and unsaved
buffers are untouched by any of it.

Missing/stopped service, older protocol or missing editor capability are
shown as errors.

## Context and tools

Each question carries its explicit project, active file/cursor/nearby unsaved
text (bounded to 16K), up to 4K of existing project instructions, and mode.
No repository map dump, new embeddings or private project-memory database is
created. Central Mike keeps conversation and generic account memory. A path
or remembered intention never proves current file content. The current IDE
has a cursor but no selection range: no invented selection is supplied.

The service binds three ephemeral tools to this original editor session/turn:

- `ReadBuffer`: current unsaved content, including hidden file panes, or an
  existing project file. Returns a turn-bound revision and disk/unsaved status;
  files above 16K text length are reported too large, not silently truncated
  into an editable replacement.
- `SearchProject`: existing project ripgrep/search. Disk matches are evidence;
  read the current buffer before editing it. No vector index is assumed.
- `EditBuffer`: an existing project file, exact read revision, replacement
  content and explicit `save`. Mode and both buffer/disk checks apply again at
  acceptance. The first version does not advertise buffer creation/deletion or
  selections that this tool interface does not expose.

Ask and Plan receive read/search tools only; the central catalogue omits
terminal and write actions for these turns. Edit proposes the change in the
existing diff tab: `a` accepts, `r` rejects. Auto applies through the same
revision fence, without a redundant diff approval. Other service operations in
Edit/Auto still need their usual grants/approvals; switching mode does not
create or widen a grant. Plan uses the normal Alt+G go-ahead flow.

`save=false` changes only the buffer and leaves it dirty; `save=true` writes
only when the buffer and disk match their checked versions. Disk changes since
the buffer was opened must be reconciled before an automated save. A user edit
while the diff waits makes acceptance fail with a conflict; re-read/replan,
never overwrite the newer buffer. A failed save reports a changed buffer,
not a saved file. Ctrl+Z undoes a Mike buffer change as one native editor edit;
putting that undo on disk needs an explicit save. The existing grouped
"Undo AI Changes" belongs to other provider paths, not Mike's buffer edits.

Clean buffers refresh from service-originated disk changes when the turn ends;
dirty buffers remain intact and keep their baseline so an automated save cannot
silently overwrite a divergent disk version. Filesystem checks happen just
before save; they are not an OS-wide atomic transaction or a lock against an
uncooperative process writing at that exact instant. Terminal commands retain
the shared service's documented OS-user boundary, not an imaginary workspace
sandbox. They operate on disk, not on unsaved IDE buffers.

## Voice input

With `"ai.voice.provider": "mike"` — or `"auto"` while the IDE is signed
in — Ctrl+Shift+Space's recording is heard by Mike: `mike_bridge.py
--hear` checks the IDE account against the service exactly as a question
does, sends the WAV to the service's `POST /v1/chat/hear`, and the service
hands it to Mike's `Hear` with its own session (the token never reaches
IDE). The words come back into the chat's box; nothing is asked of Mike
until Enter, so a spoken question and a typed one take the same road. A
minute of audio at most; nothing is kept. A service older than this route
says so ("too old to hear; upgrade it"). Signed out, `auto` hears offline
instead (see the README).

## Decisions and lifetime

Structured progress and real questions use the existing chat/status/diff UI.
The transport wakes the IDE through a hidden PTY, but business events are JSON
protocol data, not parsed CLI output. Source/model text is not treated as a
protocol command. No agent or permission loop is duplicated in the provider:
central Mike decides the next step; IDE only implements its actual editor
operations. A question keeps its turn/version and does not replace an unrelated
save/open prompt. Enter in a question prompt is not approval.

Only the original registered service session may return editor results. A
same-account CLI/client explicitly resuming the turn does not inherit editor
capabilities. Duplicate result delivery is acknowledged without executing the
edit again. IDE also remembers handled request ids before dispatch. Reads and
revisions are bound to project, chat and central turn; mode/provider/project
changes cannot apply old proposals. Closing/switching detaches editor tools,
leaves the common service and other clients alive and does not replay writes.

The central editor lease lasts 45 seconds and is renewed only by the original
service binding's progress calls; the ordinary central turn tick expires it.
This covers a killed IDE/adapter or network loss when a close message cannot
arrive. A normal detach closes immediately. Accepted external commands may
still finish; a disconnect is not a promise to roll back effects or resume
instructions after a restart. An account-generation failure clears the active
Mike conversation before more replies; older idle local views are not sent to
another account as context. They remain OS-user-local until reused/closed.

The adapter reads only structured request/reply files under the IDE's private
runs directory (0700), and opens event files 0600. A trusted custom transport
path may be set as `ai.providers.mike.bridge` or `IDE_MIKE_BRIDGE` for testing;
it is executable client code and has the same trust as the user's IDE config.

## Validation

- `code v2.14.5 test tests`: 8 native IDE fixtures, including existing CLI-agent
  and local-model regressions and `tests/mike.code` (buffers, conflicts, save,
  undo, modes, versioned questions, account reset).
- `python3 -m unittest discover -s tools -p test_mike_bridge.py`: structured
  missing-service/protocol errors, no secret output or silent start; the
  sign-in handoff (state, origin, one use, cancel, refused, mismatch, switch,
  no approvals) and the per-question account checks.
- `tests/account.code`: the Account commands, cancel, sign-out ending a Mike
  turn with the unsaved buffer kept.
- `tools/mike-login-e2e.py` (and `E2E_PHASE=expiry` on a stack up with
  `--token-seconds 90`): a CDLVSM-shaped install (released mike-service,
  no systemd bus, no Desktop/CLI) signing in through the real connect page in
  Chromium, a live Mike edit, then offline, refused account, refresh, explicit
  switch, revocation, expiry and sign-out on the real service — see ticket 168.
- `tools/mike-e2e.py`: real IDE binary/PTY, local service, central Mike/model,
  live buffer read, existing diff acceptance and buffer-only result against an
  isolated scratch stack. See ticket 162 for actual results and limitations.

The IDE/service use their existing ABI1 pins and Code 2.14.5 in these checks;
central Mike uses the workspace's newer ABI2 toolchain. No global runtime
configuration or installed packages are changed by the tests.
