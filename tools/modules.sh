#!/bin/sh
# Build the five modules the ide links, from a checkout of codelovesme/code
# at CODE_REF, into <out>/<name>.so.
#
#   tools/modules.sh <code-checkout> <out>
set -eu
code_dir=$1
out=$2
mkdir -p "$out"
for m in env fs strings syntax tty; do
  (cd "$code_dir/crates/modules/$m" && cargo build --release --quiet)
  cp "$code_dir/crates/modules/$m/target/release/lib$m.so" "$out/$m.so"
done
