// Game-thread performance: APerformanceHint and the fast-core switch.
#pragma once

#include <stdint.h>

// Game thread, once: finds the fast cores and opens the hint session.
void PerfStart(int64_t target_ns);
// The game work of one loop iteration (frames run, not the vsync wait).
void PerfReport(int64_t work_ns);
// About twice a second: applies the fast-core setting to every thread again
// (the background cpuset replaces the masks and they are not restored).
void PerfCheckCores(void);
