// Second game: DKC2Recomp runner (upstream/game2).
#include "core_game.h"
#include "monoloco_core.h"

#include "common_cpu_infra.h"
#include "common_rtl.h"
#include "dkc2_game.h"
#include "dkc2_kongs.h"
#include "dkc2_music.h"
#include "dkc2_video.h"
#include "verified_rom.h"

static Dkc2VideoAspect Aspect(int aspect) {
  switch (aspect) {
    case kMonolocoAspect16x10: return kDkc2VideoAspect16x10;
    case kMonolocoAspect16x9: return kDkc2VideoAspect16x9;
    default: return kDkc2VideoAspectNative;
  }
}

uint8_t *GameReadVerifiedRom(const char *path, size_t *size, char *error,
                             size_t error_size) {
  return Dkc2ReadVerifiedRom(path, size, error, error_size);
}

bool GameStart(uint8_t *rom, size_t size, int aspect) {
  Dkc2VideoSetAspect(Aspect(aspect));
  // Same order as the desktop hosts: character packs and music before boot.
  Dkc2KongsInitialize();
  Dkc2MusicInitialize();
  RtlRegisterGame(Dkc2GameInfo());
  return SnesInit(rom, (int)size) != NULL;
}

void GameSetAspect(int aspect) { Dkc2VideoSetAspect(Aspect(aspect)); }
int GameWidth(void) { return Dkc2VideoWidth(); }
void GameBeginDrawing(uint8_t *pixels, size_t pitch) { Dkc2BeginDrawing(pixels, pitch); }
void GameDrawFrame(void) { Dkc2DrawPpuFrame(); }
bool GameFrameOk(void) { return Dkc2LastLleResult() != 0; }
