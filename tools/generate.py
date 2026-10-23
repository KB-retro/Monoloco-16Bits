#!/usr/bin/env python3
"""Generates one game's C sources from the player's own ROM, with that game's
upstream generator (upstream/gameN/scripts/generate_snesrecomp.py).

The output lands in upstream/gameN/generated/snesrecomp, which the upstream
projects already keep out of Git. Nothing generated is ever committed here.

    python3 tools/generate.py --game 1 --rom /private/path/rom.sfc
"""
import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHA256 = {
    1: "fa8cacf5bbfc39ee6bbaa557adf89133d60d42f6cf9e1db30d5a36a469f74d15",
    2: "35421a9af9dd011b40b91f792192af9f99c93201d8d394026bdfb42cbf2d8633",
    3: "2277a2d8dddb01fe5cb0ae9a0fa225d42b3a11adccaeafa18e3c339b3794a32b",
}
ROM_SIZE = 4 * 1024 * 1024
HEADER = 512


def generated_dir(game: int) -> Path:
    return ROOT / "upstream" / f"game{game}" / "generated" / "snesrecomp"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--game", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--backend", choices=("native", "python"),
                        help="analysis backend (default: native when cargo is available)")
    args = parser.parse_args()

    data = args.rom.expanduser().read_bytes()
    if len(data) == ROM_SIZE + HEADER:
        data = data[HEADER:]
    if len(data) != ROM_SIZE or hashlib.sha256(data).hexdigest() != SHA256[args.game]:
        print(f"error: {args.rom} is not the supported ROM of game {args.game}", file=sys.stderr)
        return 1

    upstream = ROOT / "upstream" / f"game{args.game}"
    script = upstream / "scripts" / "generate_snesrecomp.py"
    if not script.is_file():
        print("error: submodules missing; run git submodule update --init --recursive", file=sys.stderr)
        return 1
    backend = args.backend or ("native" if shutil.which("cargo") else "python")
    output = generated_dir(args.game)
    # A fresh output: stale translation units would otherwise be compiled too.
    if output.exists():
        shutil.rmtree(output)
    with tempfile.TemporaryDirectory(prefix="monoloco-rom-") as private:
        rom = Path(private) / "rom.sfc"  # headerless copy, deleted afterwards
        rom.write_bytes(data)
        command = [sys.executable, str(script), "--rom", str(rom), "--analysis-backend", backend]
        print("+", " ".join(command), flush=True)
        result = subprocess.run(command, cwd=upstream)
    if result.returncode != 0:
        return result.returncode
    if not any(output.glob("*.c")):
        print(f"error: the generator wrote no sources to {output}", file=sys.stderr)
        return 1
    print(f"game {args.game}: generated sources in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
