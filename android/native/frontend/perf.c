// Keeps the game thread fast: an APerformanceHint session (Android 13+,
// looked up at run time) and, optionally, every thread on the fastest CPU
// cluster. Adapted from KB-retro's NFSU-X port (android_perf_hint.c): some
// power-saving profiles move a game onto the little cores, and coming back
// from the background leaves every thread there.
#define _GNU_SOURCE
#include "perf.h"
#include "frontend.h"

#include <android/log.h>
#include <dirent.h>
#include <dlfcn.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/syscall.h>
#include <unistd.h>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "Monoloco", __VA_ARGS__)

typedef struct APerformanceHintManager APerformanceHintManager;
typedef struct APerformanceHintSession APerformanceHintSession;
typedef APerformanceHintManager *(*GetManagerFn)(void);
typedef APerformanceHintSession *(*CreateSessionFn)(APerformanceHintManager *, const int32_t *, size_t, int64_t);
typedef int (*ReportFn)(APerformanceHintSession *, int64_t);

static APerformanceHintSession *s_session;
static ReportFn s_report;
static cpu_set_t s_fast, s_all;
static int s_fast_count;
static bool s_applied_fast;

// The cores whose maximum frequency is at least 80% of the fastest one.
static void FindFastCores(void) {
  long freq[64], best = 0;
  int n = 0;
  for (int i = 0; i < 64; i++) {
    char path[96];
    snprintf(path, sizeof path, "/sys/devices/system/cpu/cpu%d/cpufreq/cpuinfo_max_freq", i);
    freq[i] = 0;
    FILE *file = fopen(path, "r");
    if (!file) continue;
    if (fscanf(file, "%ld", &freq[i]) != 1) freq[i] = 0;
    fclose(file);
    if (freq[i] > best) best = freq[i];
    n = i + 1;
  }
  CPU_ZERO(&s_fast);
  CPU_ZERO(&s_all);
  for (int i = 0; i < n; i++) {
    if (freq[i]) CPU_SET(i, &s_all);
    if (best && freq[i] * 10 >= best * 8) {
      CPU_SET(i, &s_fast);
      s_fast_count++;
    }
  }
  LOGI("fast cores: %d of %d at >= %ld MHz", s_fast_count, n, best * 8 / 10 / 1000);
}

// Every thread of the process (game, audio, SDL) gets the same mask.
static int ApplyAllThreads(const cpu_set_t *want) {
  DIR *tasks = opendir("/proc/self/task");
  if (!tasks) return 0;
  int fixed = 0;
  struct dirent *entry;
  while ((entry = readdir(tasks)) != NULL) {
    pid_t tid = (pid_t)atoi(entry->d_name);
    cpu_set_t now;
    if (tid <= 0) continue;
    if (sched_getaffinity(tid, sizeof now, &now) == 0 && CPU_EQUAL(&now, want)) continue;
    if (sched_setaffinity(tid, sizeof *want, want) == 0) fixed++;
  }
  closedir(tasks);
  return fixed;
}

void PerfStart(int64_t target_ns) {
  FindFastCores();
  void *library = dlopen("libandroid.so", RTLD_NOW);
  GetManagerFn get_manager = library ? (GetManagerFn)dlsym(library, "APerformanceHint_getManager") : NULL;
  CreateSessionFn create = library ? (CreateSessionFn)dlsym(library, "APerformanceHint_createSession") : NULL;
  s_report = library ? (ReportFn)dlsym(library, "APerformanceHint_reportActualWorkDuration") : NULL;
  if (!get_manager || !create || !s_report) {
    LOGI("APerformanceHint unavailable (Android 12 or older)");
    return;
  }
  APerformanceHintManager *manager = get_manager();
  int32_t tid = (int32_t)syscall(SYS_gettid);
  s_session = manager ? create(manager, &tid, 1, target_ns) : NULL;
  LOGI("APerformanceHint session %s", s_session ? "active" : "refused");
}

void PerfReport(int64_t work_ns) {
  if (s_session && work_ns > 0) s_report(s_session, work_ns);
}

void PerfCheckCores(void) {
  if (!CPU_COUNT(&s_all)) return;
  bool fast = atomic_load(&g_frontend.fast_cores) && s_fast_count > 0;
  const cpu_set_t *want = fast ? &s_fast : &s_all;
  cpu_set_t now;
  // Cheap when nothing changed: only this thread's mask is read.
  if (fast == s_applied_fast && sched_getaffinity(0, sizeof now, &now) == 0 && CPU_EQUAL(&now, want)) return;
  int fixed = ApplyAllThreads(want);
  if (fast != s_applied_fast || fixed) LOGI("cores: %s (%d threads)", fast ? "fast" : "all", fixed);
  s_applied_fast = fast;
}
