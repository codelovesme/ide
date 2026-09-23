#!/bin/sh
# Build the ide as a program and lay the release bundle out:
#
#   ide-<version>-x86_64-linux/
#     ide            the launcher (bin/ide)
#     ide-bin        the program, built by `code build`
#     *.so           the organelles `euglena install` fetched, beside it
#     VERSION, README.md
#
# The program is main.code without its organelle links: those would be
# built in as full paths on this machine, so the ide links its organelles
# itself while it runs (see Organelles in src/ide.gene.code).
#
#   tools/package.sh <version> <out-dir>        (after `euglena test`)
set -eu
version=$1
out=$2
root=$(cd "$(dirname "$0")/.." && pwd)
[ -f "$root/main.code" ] || { echo "no main.code — run euglena test first" >&2; exit 1; }
name="ide-$version-x86_64-linux"
stage="$out/$name"
rm -rf "$stage"
mkdir -p "$stage"
grep -v '^link ".*\.so"' "$root/main.code" | grep -v '^| ' > "$root/standalone.code"
(cd "$root" && cdlvsm code build standalone.code -r -o "$stage/ide-bin")
rm -f "$root/standalone.code"
cp "$root/bin/ide" "$stage/ide"
cp "$root/README.md" "$stage/"
"$root/tools/organelles.sh" "$stage"
echo "$version" > "$stage/VERSION"
tar -C "$out" -czf "$out/$name.tar.gz" "$name"
echo "$out/$name.tar.gz"
