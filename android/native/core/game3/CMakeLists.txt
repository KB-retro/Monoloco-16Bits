# Game 3: mirrors upstream/game3's dkc3_snesrecomp_headless target, including
# its build-directory runtime copies (cmake/Dkc3RuntimePatches.cmake).
set(UPSTREAM ${MONOLOCO_UPSTREAM}/game3)
monoloco_generated_sources(3 GENERATED)
if(NOT GENERATED AND NOT MONOLOCO_CHECK_CORES)
    message(STATUS "Monoloco: no generated sources for game 3; core skipped")
    return()
endif()
set(SNESRECOMP_ROOT ${UPSTREAM}/snesrecomp)
include(${SNESRECOMP_ROOT}/runner/runner.cmake)

find_package(Python3 COMPONENTS Interpreter REQUIRED)
set(_patched_dir "${CMAKE_CURRENT_BINARY_DIR}/dkc3-runtime")
execute_process(
    COMMAND "${Python3_EXECUTABLE}" "${UPSTREAM}/scripts/apply_dkc3_runtime_patches.py"
        --patches "${UPSTREAM}/cmake/runtime-patches"
        --snesrecomp "${SNESRECOMP_ROOT}"
        --out "${_patched_dir}"
    RESULT_VARIABLE result ERROR_VARIABLE error_text)
if(NOT result EQUAL 0)
    message(FATAL_ERROR "Game 3 runtime adaptation failed:\n${error_text}")
endif()
file(GLOB _hunks CONFIGURE_DEPENDS "${UPSTREAM}/cmake/runtime-patches/*.hunks")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${_hunks})
file(STRINGS "${_patched_dir}/manifest.txt" _manifest)
foreach(line IN LISTS _manifest)
    string(REPLACE "\t" ";" pair "${line}")
    list(GET pair 0 original)
    list(GET pair 1 patched)
    list(FIND SNESRECOMP_RUNNER_SOURCES "${original}" index)
    if(index EQUAL -1)
        message(FATAL_ERROR "Game 3 runtime patch targets ${original}, not a runtime source")
    endif()
    list(REMOVE_ITEM SNESRECOMP_RUNNER_SOURCES "${original}")
    list(APPEND SNESRECOMP_RUNNER_SOURCES "${patched}")
endforeach()

monoloco_strip_desktop_sources(SNESRECOMP_RUNNER_SOURCES ${SNESRECOMP_ROOT})
set(RUNNER
    dkc3_game.c dkc3_video.c dkc3_hdma.c dkc3_spc_music.c
    headless_host.c input_playback.c verified_rom.c)
list(TRANSFORM RUNNER PREPEND ${UPSTREAM}/runner/)
set(INCLUDES ${UPSTREAM}/runner ${UPSTREAM}/recomp ${SNESRECOMP_RUNNER_INCLUDE_DIRS})
if(GENERATED)
    monoloco_add_core(3 SOURCES ${SNESRECOMP_RUNNER_SOURCES} ${GENERATED} ${RUNNER}
        INCLUDES ${INCLUDES})
else()
    monoloco_check_funcs_header(${UPSTREAM} ${CMAKE_CURRENT_BINARY_DIR}/check)
    monoloco_add_core(3 CHECK SOURCES ${SNESRECOMP_RUNNER_SOURCES} ${RUNNER}
        INCLUDES ${CMAKE_CURRENT_BINARY_DIR}/check ${INCLUDES})
endif()
