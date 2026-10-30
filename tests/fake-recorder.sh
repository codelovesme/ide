#!/bin/sh
# A stand-in for pw-record in the tests: the last argument is the file. It
# writes a second of 16 kHz silence as a WAV and waits to be stopped
# (Ctrl+C), the way pw-record does — then exits 1, as pw-record does.
for out in "$@"; do :; done
{ printf 'RIFF'; head -c 32040 /dev/zero; } > "$out"
trap 'exit 1' INT TERM
sleep 30 &
wait $!
