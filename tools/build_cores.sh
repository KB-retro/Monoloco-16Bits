#!/usr/bin/env bash
# Builds game cores on your PC, from your own ROMs, to import into an installed
# Monoloco Saga: copy the .so files next to your ROMs and press "Change folder".
# The cores hold code generated from the game: keep them to yourself.
#
#   ANDROID_NDK=/path/to/ndk tools/build_cores.sh --rom1 game1.sfc [--rom2 ...] [--rom3 ...]
set -euo pipefail
cd "$(dirname "$0")/.."

declare -A ROMS=()
OUT=build/cores
while [ $# -gt 0 ]; do
  case "$1" in
    --rom1|--rom2|--rom3) ROMS[${1#--rom}]="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    *) echo "usage: $0 --rom1 FILE [--rom2 FILE] [--rom3 FILE] [--out DIR]" >&2; exit 2 ;;
  esac
done
[ ${#ROMS[@]} -gt 0 ] || { echo "Give at least one --romN." >&2; exit 2; }
NDK="${ANDROID_NDK:-${ANDROID_NDK_HOME:-}}"
[ -f "$NDK/build/cmake/android.toolchain.cmake" ] || { echo "Set ANDROID_NDK to an NDK (30.0.16248370)." >&2; exit 2; }

ARGS=()
TARGETS=()
for game in "${!ROMS[@]}"; do
  python3 tools/generate.py --game "$game" --rom "${ROMS[$game]}"
  ARGS+=("-DMONOLOCO_GAME${game}_GEN_DIR=$PWD/upstream/game$game/generated/snesrecomp")
  TARGETS+=("monoloco_game$game")
done

BUILD=build/cores-build
cmake -S android/native -B "$BUILD" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$NDK/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-30 \
  -DCMAKE_BUILD_TYPE=Release -DMONOLOCO_CORES_ONLY=ON "${ARGS[@]}"
cmake --build "$BUILD" --target "${TARGETS[@]}"
mkdir -p "$OUT"
for target in "${TARGETS[@]}"; do
  find "$BUILD" -name "lib$target.so" -exec cp {} "$OUT/" \;
done
echo "Cores in $OUT:"
ls -l "$OUT"
