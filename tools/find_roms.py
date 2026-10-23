#!/usr/bin/env python3
"""Finds the three supported ROMs in a folder or .zip by size and SHA-256,
whatever their names, and prints `monoloco.romN=<path>` lines for
local.properties. ROMs found in a .zip are extracted next to it.

    python3 tools/find_roms.py /private/folder-or-archive >> local.properties
"""
import hashlib
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import HEADER, ROM_SIZE, SHA256  # noqa: E402


def game_of(data: bytes) -> int:
    if len(data) == ROM_SIZE + HEADER:
        data = data[HEADER:]
    if len(data) != ROM_SIZE:
        return 0
    digest = hashlib.sha256(data).hexdigest()
    return next((game for game, sha in SHA256.items() if sha == digest), 0)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    source = Path(sys.argv[1])
    found = {}
    unknown = 0
    if source.is_file() and zipfile.is_zipfile(source):
        # A download may have no extension: never reuse the archive's own name.
        out = source.parent / (source.name + ".roms")
        out.mkdir(exist_ok=True)
        with zipfile.ZipFile(source) as archive:
            for info in archive.infolist():
                if info.is_dir() or info.file_size not in (ROM_SIZE, ROM_SIZE + HEADER):
                    continue
                data = archive.read(info)
                game = game_of(data)
                if not game:
                    unknown += 1
                    continue
                path = out / f"game{game}.sfc"
                path.write_bytes(data)
                found.setdefault(game, path)
    else:
        files = [source] if source.is_file() else sorted(p for p in source.rglob("*") if p.is_file())
        for path in files:
            if path.stat().st_size not in (ROM_SIZE, ROM_SIZE + HEADER):
                continue
            game = game_of(path.read_bytes())
            if game:
                found.setdefault(game, path)
            else:
                unknown += 1
    for game in sorted(found):
        print(f"monoloco.rom{game}={found[game]}")
    print(f"found games {sorted(found)}; unrecognised 4 MB files: {unknown}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
