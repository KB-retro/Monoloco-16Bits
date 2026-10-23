# Third-party notices

Monoloco Saga contains no ROM, generated game code, compiled game cores,
extracted graphics, music or save data. Users supply their own ROMs.

| Component | Location | License |
|---|---|---|
| DKC1Recomp (elliotttate and contributors) | `upstream/game1` | MIT, see `upstream/game1/LICENSE` and `upstream/game1/THIRD_PARTY_NOTICES.md` |
| DKC2Recomp (elliotttate and contributors) | `upstream/game2` | MIT, see `upstream/game2/LICENSE` and `upstream/game2/THIRD_PARTY_NOTICES.md` |
| DKC3Recomp (elliotttate and contributors) | `upstream/game3` | MIT, see `upstream/game3/LICENSE` and `upstream/game3/THIRD_PARTY_NOTICES.md` |
| snesrecomp (pinned separately by each project above) | `upstream/gameN/snesrecomp` | PolyForm Noncommercial 1.0.0, see its `LICENSE` and `THIRD_PARTY_ATTRIBUTION.md` |
| SDL 2.32.10 | `android/SDL` | zlib, see `android/SDL/LICENSE.txt` |

The structural metadata in the upstream `recomp/*.cfg` files derives from
GPL-3 community disassemblies, as recorded by each upstream project. The
snesrecomp engine is noncommercial: Monoloco Saga is free and must not be
sold.

The HD filter is the Reconstruct upscaler of DKC2Recomp (MIT), compiled from
`upstream/game2/runner/desktop_reconstruct_shader.h` and only translated to
GLSL ES 3 at run time.

The touch-control editor, quick menu and launcher follow KB-retro's own
NFSU-X and G-Zero 64 Android ports.

Game names and trademarks belong to their respective owners. This is an
unofficial noncommercial fan project.
