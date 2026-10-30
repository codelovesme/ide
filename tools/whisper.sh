#!/bin/sh
# Build whisper.cpp's whisper-cli — the offline voice input's ears (see
# src/voice.gene.code) — pinned, with no shared libraries of its own, into
# <out> (default organelles/, where a checkout's ide looks for it; the
# release bundle carries it beside the program).
#
#   tools/whisper.sh [out]
#
# Needs git, cmake and a C++ compiler. The source is fetched once into
# .whisper-build/ (or $WHISPER_BUILD_DIR) and checked against the pinned
# commit. Built for x86-64 with AVX2 (any CPU from about 2013 on).
set -eu
version=v1.9.5
commit=d1be6fde11ac6e0407606b4e42fe72d34add8037
root=$(cd "$(dirname "$0")/.." && pwd)
out=${1:-$root/organelles}
work=${WHISPER_BUILD_DIR:-$root/.whisper-build}
mkdir -p "$out" "$work"
if [ ! -d "$work/src/.git" ]; then
  git -c advice.detachedHead=false clone -q --depth 1 --branch "$version" https://github.com/ggml-org/whisper.cpp "$work/src"
fi
got=$(git -C "$work/src" rev-parse HEAD)
[ "$got" = "$commit" ] || { echo "whisper.cpp $version is $got, not the pinned $commit" >&2; exit 1; }
cmake -S "$work/src" -B "$work/build" -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF -DGGML_NATIVE=OFF -DGGML_OPENMP=OFF \
  -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_SERVER=OFF \
  -DCMAKE_EXE_LINKER_FLAGS="-static-libstdc++ -static-libgcc" > "$work/cmake.log"
cmake --build "$work/build" -j"$(nproc)" --target whisper-cli > "$work/build.log"
cp "$work/build/bin/whisper-cli" "$out/whisper-cli"
echo "$out/whisper-cli"
