# Game 1: mirrors upstream/game1's dkc1_snesrecomp_headless target.
set(UPSTREAM ${MONOLOCO_UPSTREAM}/game1)
monoloco_generated_sources(1 GENERATED)
if(NOT GENERATED AND NOT MONOLOCO_CHECK_CORES)
    message(STATUS "Monoloco: no generated sources for game 1; core skipped")
    return()
endif()
set(SNESRECOMP_ROOT ${UPSTREAM}/snesrecomp)
include(${SNESRECOMP_ROOT}/runner/runner.cmake)
monoloco_strip_desktop_sources(SNESRECOMP_RUNNER_SOURCES ${SNESRECOMP_ROOT})
set(RUNNER
    desktop_sram.c dkc1_game.c dkc1_video.c dkc1_baby_kong.c
    dkc1_baby_kong_animation.c dkc1_baby_kong_movement.c dkc1_dixie_mod.c
    dkc1_margin_proxy.c dkc1_ws_trace.c input_playback.c wram_dump.c
    dkc1_script.c dkc1_debug_dump.c dkc1_flight_recorder.c dkc1_blank_scan.c
    dkc1_invariant_monitor.c verified_rom.c headless_host.c)
list(TRANSFORM RUNNER PREPEND ${UPSTREAM}/runner/)
set(INCLUDES ${UPSTREAM}/runner ${UPSTREAM}/recomp ${SNESRECOMP_RUNNER_INCLUDE_DIRS})
set(DEFINITIONS DKC1_BUILD_COMMIT="monoloco" DKC1_BUILD_CONFIG="android")
if(GENERATED)
    monoloco_add_core(1 SOURCES ${SNESRECOMP_RUNNER_SOURCES} ${GENERATED} ${RUNNER}
        INCLUDES ${INCLUDES} DEFINITIONS ${DEFINITIONS})
else()
    monoloco_check_funcs_header(${UPSTREAM} ${CMAKE_CURRENT_BINARY_DIR}/check)
    monoloco_add_core(1 CHECK SOURCES ${SNESRECOMP_RUNNER_SOURCES} ${RUNNER}
        INCLUDES ${CMAKE_CURRENT_BINARY_DIR}/check ${INCLUDES} DEFINITIONS ${DEFINITIONS})
endif()
