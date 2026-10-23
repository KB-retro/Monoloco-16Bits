// Interface between the Android frontend (libmain.so) and one game core
// (libmonoloco_gameN.so). Each core carries its own snesrecomp revision, so
// only this C table crosses the library boundary. Every call happens on the
// frontend's game thread.
#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Raised whenever the table changes; the frontend refuses other versions, so an
// imported core built from an older checkout fails cleanly instead of crashing.
#define MONOLOCO_CORE_ABI 1

enum {
  kMonolocoAspectNative = 0,  // 256 pixels wide
  kMonolocoAspect16x10 = 1,
  kMonolocoAspect16x9 = 2,
  kMonolocoAspectCount = 3,
};

enum { kMonolocoVideoHeight = 224, kMonolocoVideoMaxWidth = 448 };

typedef struct MonolocoCore {
  int abi;
  int game;  // 1, 2 or 3
  // Loads the verified ROM and the battery save from save_dir (the core makes
  // it its working directory). Returns 0 and fills error on failure.
  int (*load)(const char *rom_path, const char *save_dir, int aspect,
              int audio_rate, char *error, size_t error_size);
  // Applies at the next frame; the width changes with it.
  void (*set_aspect)(int aspect);
  int (*width)(void);
  // One guest frame with the packed controller bits of both players.
  // Returns 0 when the runtime stopped.
  int (*run_frame)(uint32_t input);
  // BGRA pixels of the last frame, width() * kMonolocoVideoHeight.
  const uint8_t *(*pixels)(void);
  // Interleaved stereo for the time of one frame.
  void (*render_audio)(int16_t *samples, int frames);
  // Writes the battery save if it changed (always when force is set).
  void (*flush_save)(int force);
  int (*save_state)(const char *path);
  int (*load_state)(const char *path);
} MonolocoCore;

typedef const MonolocoCore *(*MonolocoCoreEntry)(void);
#define MONOLOCO_CORE_SYMBOL "monoloco_core"

#ifdef __cplusplus
}
#endif
