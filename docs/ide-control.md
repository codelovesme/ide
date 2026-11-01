# Local IDE control, protocol 1

Each IDE process creates a random session identity and credential, listens on
`127.0.0.1` with an OS-assigned port, and publishes a private `session.json`
inside a `0700` temporary directory. Credentials never enter model context.
Terminal children receive `TERM_PROGRAM=codelovesme-ide`,
`CODELOVESME_IDE_SESSION`, `CODELOVESME_IDE_SESSION_FILE`,
`CODELOVESME_IDE_TERMINAL` and `CODELOVESME_IDE_HELPER`. A per-session bin
directory prefixes PATH with `claude`, `codex` and `ide-control` adapters.
A terminal's stable control identifier is independent of its OS process/PTY id.
It survives a move or resize and is never reassigned within the IDE session.

Clients read the private descriptor, verify the listener belongs to this OS
user, then POST JSON to `/v1/control` with `Authorization: Bearer <credential>`:

```json
{"version":1,"session":"<instance>","terminal":"terminal-1","action":"move","slot":"l"}
```

Actions are `state`, `move` (`slot`: `l r t b c tl tr bl br`) and `resize`
(`delta`: integer -20..20). State is read-only; other actions require an exact
visible terminal identifier. State includes the current project, terminal tabs,
slots, active/hidden flags, pane rectangles, track settings and screen size.
It excludes document contents and model conversation. Errors return JSON with
`ok:false`/`error`, a non-200 status, and no change to layout for invalid input.
The same event queue handles keys and control requests. Moves reuse MoveCurrent;
resizing uses the existing settings/layout and PTY resize path. The target tab
is revealed and takes focus for a successful layout operation. Track resizing
is shared with panes occupying that track; the returned rectangle is the
actual visible result, which may differ from the requested track size.

`tools/ide_control.py mcp` implements newline-delimited JSON-RPC stdio MCP:
initialize (with live session context in server instructions), tools/list,
tools/call and ping. Tools are `ide_state`, `ide_move_terminal` and
`ide_resize_terminal`; the origin is implicit in that adapter's environment.
The Claude launcher appends context and adds this server per invocation.
Codex receives this server via per-invocation `-c` overrides and gets context
through MCP initialization instructions; it does not replace user instructions.
Both resolve the actual CLI after excluding all IDE adapter bin directories,
including those inherited through nested IDE launches. Bash reads the existing
user bashrc through a session-local rc file, then prepends adapters after any
PATH changes in that file. Other shells inherit the adapter PATH; custom
startup code must keep it ahead of the vendor CLI directory. Help/version pass
through. Direct absolute CLI paths and shell aliases/functions can bypass
adapters. Tools always query live state rather than a cached launch snapshot.

Mike's client refreshes context through the helper before each submitted turn.
Its shared service runs the helper as an approved terminal step with an explicit
session-file path and terminal id. There is no change to service credentials,
account state or command permissions. Existing/resumed work retains its
original target rather than being rewritten for a different IDE.

Normal quit stops the control listener and deletes the descriptor/adapters.
Crashes can leave a private temporary directory: its old port/key/identity
cannot control a new IDE. If the port is reused by another user the client
refuses it before sending credentials; another IDE owned by this user rejects
the old key/session. No automatic discovery picks a replacement target.
Starting an IDE outside the package still uses the same helper in tools/.
Without Python, the editor still opens and reports control as unavailable.

Verification:

```sh
python3 tools/control_smoke.py <bundle>/ide
IDE_TEST_AGENTS=1 python3 tools/control_smoke.py <bundle>/ide
IDE_TEST_MIKE=1 python3 tools/control_smoke.py <bundle>/ide
```

The first needs no model/network account. The second invokes installed Claude
and Codex against a disposable IDE/project. The third additionally uses the
currently signed-in local Mike service and creates a test conversation; it
approves only the exact layout helper commands in the temporary IDE. It never
changes account, grants or real project files. Both optional modes use model
requests. Release CI runs the first mode on the packaged executable.

The IDE's existing source/imports require the release workflow's pinned Code
v2.14.5. Newer Code import semantics are a separate migration; do not silently
upgrade that pin. For a local package build use `CODE_BIN=/path/to/v2.14.5/code
 tools/package.sh dev-control /absolute/output/path`.
