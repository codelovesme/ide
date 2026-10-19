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

Start/sign in to the shared service first. Existing Desktop pairing/session
can be reused. IDE plus service is sufficient: alternatively load an account
session token into `MIKE_IDE_TOKEN` from a protected environment before IDE
starts. The transport passes it to the service for normal account verification,
never to settings, project files, the model, command arguments or event logs.
Never paste credentials into a shell command. A headless device enrollment
alone is not permission to read an account's chat. Missing/stopped service,
older protocol, missing editor capability or refused sign-in are shown as
errors; IDE does not install/start a different service to conceal them.

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
  missing-service/protocol errors, no secret output or silent start.
- `tools/mike-e2e.py`: real IDE binary/PTY, local service, central Mike/model,
  live buffer read, existing diff acceptance and buffer-only result against an
  isolated scratch stack. See ticket 162 for actual results and limitations.

The IDE/service use their existing ABI1 pins and Code 2.14.5 in these checks;
central Mike uses the workspace's newer ABI2 toolchain. No global runtime
configuration or installed packages are changed by the tests.
