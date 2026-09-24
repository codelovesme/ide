#!/bin/sh
# A stand-in for `claude -p … --output-format stream-json` in the tests:
# the same kind of events, at once. It notes its arguments, and in edit
# mode (acceptEdits) changes hello.code and makes new.txt. A question with
# "slow" in it waits, to be stopped.
printf '%s\n' "$*" > "${TMPDIR:-/tmp}/ide-fake-agent-args"
prompt=$(cat)
case "$prompt" in *slow*) sleep 30 ;; esac
here=$(pwd)
echo '{"type":"system","subtype":"init","session_id":"fake-session"}'
case "$*" in *acceptEdits*)
  echo 'Hello again' >> hello.code
  echo new > new.txt
  echo '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"'"$here"'/hello.code"}}]}}'
  ;;
esac
echo '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"'"$here"'/hello.code"}}]}}'
echo '{"type":"assistant","message":{"content":[{"type":"text","text":"It greets."}]}}'
echo '{"type":"result","subtype":"success","is_error":false,"session_id":"fake-session","result":"It greets."}'
