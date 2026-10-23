// What core_common.c needs from one game's runner (gameN.c).
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifndef MONOLOCO_GAME
#error "MONOLOCO_GAME must be 1, 2 or 3"
#endif

uint8_t *GameReadVerifiedRom(const char *path, size_t *size, char *error,
                             size_t error_size);
// Everything up to and including SnesInit.
bool GameStart(uint8_t *rom, size_t size, int aspect);
void GameSetAspect(int aspect);
int GameWidth(void);
void GameBeginDrawing(uint8_t *pixels, size_t pitch);
void GameDrawFrame(void);
bool GameFrameOk(void);
