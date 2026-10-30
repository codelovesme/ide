#!/bin/sh
# A stand-in for whisper-cli in the tests: `-of base` → base.json, in
# whisper-cli's -oj shape, with the words "open the readme" — after
# checking it was given a model and a recording that are there.
while [ $# -gt 0 ]; do
  case "$1" in
    -m) model=$2; shift ;;
    -f) wav=$2; shift ;;
    -of) base=$2; shift ;;
  esac
  shift
done
[ -s "$model" ] || { echo "error: no model at $model" >&2; exit 2; }
[ -s "$wav" ] || { echo "error: no audio at $wav" >&2; exit 2; }
printf '{"result":{"language":"en"},"transcription":[{"text":" open the"},{"text":" readme "}]}' > "$base.json"
