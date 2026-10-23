// First game: DKC1Recomp runner (upstream/game1).
#include "core_game.h"
#include "monoloco_core.h"

#include "common_cpu_infra.h"
#include "common_rtl.h"
#include "dkc1_game.h"
#include "dkc1_video.h"
#include "verified_rom.h"

#include <stdlib.h>

static Dkc1VideoAspect Aspect(int aspect) {
  switch (aspect) {
    case kMonolocoAspect16x10: return kDkc1VideoAspect16x10;
    case kMonolocoAspect16x9: return kDkc1VideoAspect16x9;
    default: return kDkc1VideoAspectNative;
  }
}

uint8_t *GameReadVerifiedRom(const char *path, size_t *size, char *error,
                             size_t error_size) {
  // Only the clean retail ROM the code was generated from.
  unsetenv("DKC1_ALLOW_ROM_SHA256");
  return Dkc1ReadVerifiedRom(path, size, error, error_size);
}

bool GameStart(uint8_t *rom, size_t size, int aspect) {
  Dkc1VideoSetAspect(Aspect(aspect));
  Dkc1VideoSetRom(rom, size);
  RtlRegisterGame(Dkc1GameInfo());
  return SnesInit(rom, (int)size) != NULL;
}

void GameSetAspect(int aspect) { Dkc1VideoSetAspect(Aspect(aspect)); }
int GameWidth(void) { return Dkc1VideoWidth(); }
void GameBeginDrawing(uint8_t *pixels, size_t pitch) { Dkc1BeginDrawing(pixels, pitch); }
void GameDrawFrame(void) { Dkc1DrawPpuFrame(); }
bool GameFrameOk(void) { return Dkc1LastLleResult() != 0; }
