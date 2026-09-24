#!/bin/sh
# Lay the organelles `euglena install` fetched out flat, as
# <out>/<name>.so — where the ide links them from while it runs
# (see Organelles in src/ide.gene.code). Default <out>: organelles/.
#
#   tools/organelles.sh [out]
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
out=${1:-$root/organelles}
mkdir -p "$out"
for m in env fs http_client json localai process pty strings syntax tty; do
  so=$(find "$root/.code/modules/$m" -name "$m-linux-x86_64.so" 2>/dev/null | head -1)
  [ -n "$so" ] || { echo "organelle $m is not installed — run: cdlvsm euglena install" >&2; exit 1; }
  cp "$so" "$out/$m.so"
done
