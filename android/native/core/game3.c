// Third game: DKC3Recomp runner (upstream/game3).
#include "core_game.h"
#include "monoloco_core.h"

#include "common_cpu_infra.h"
#include "common_rtl.h"
#include "dkc3_game.h"
#include "dkc3_video.h"
#include "verified_rom.h"

static Dkc3VideoAspect Aspect(int aspect) {
  switch (aspect) {
    case kMonolocoAspect16x10: return kDkc3VideoAspect16x10;
    case kMonolocoAspect16x9: return kDkc3VideoAspect16x9;
    default: return kDkc3VideoAspectNative;
  }
}

uint8_t *GameReadVerifiedRom(const char *path, size_t *size, char *error,
                             size_t error_size) {
  return Dkc3ReadVerifiedRom(path, size, error, error_size);
}

bool GameStart(uint8_t *rom, size_t size, int aspect) {
  Dkc3VideoSetAspect(Aspect(aspect));
  RtlRegisterGame(Dkc3GameInfo());
  return SnesInit(rom, (int)size) != NULL;
}

void GameSetAspect(int aspect) { Dkc3VideoSetAspect(Aspect(aspect)); }
int GameWidth(void) { return Dkc3VideoWidth(); }
void GameBeginDrawing(uint8_t *pixels, size_t pitch) { Dkc3BeginDrawing(pixels, pitch); }
void GameDrawFrame(void) { Dkc3DrawPpuFrame(); }
bool GameFrameOk(void) { return Dkc3LastLleResult() != 0; }
