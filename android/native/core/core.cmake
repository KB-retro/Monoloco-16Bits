# Shared pieces of the three game cores. Each gameN/CMakeLists.txt includes
# its own pinned runner.cmake first (directory scope keeps the three snesrecomp
# revisions apart), then calls monoloco_add_core().
set(MONOLOCO_CORE_DIR ${CMAKE_CURRENT_LIST_DIR})

# The private generated sources for game N, or an empty list when the build
# has no ROM for it (the APK then ships without that game).
function(monoloco_generated_sources game out_var)
    set(dir "${MONOLOCO_GAME${game}_GEN_DIR}")
    set(sources)
    if(dir AND IS_DIRECTORY "${dir}")
        file(GLOB sources CONFIGURE_DEPENDS "${dir}/*.c")
    endif()
    set(${out_var} ${sources} PARENT_SCOPE)
endfunction()

option(MONOLOCO_CHECK_CORES
    "Without generated sources, still compile each core's runner (no link)" OFF)

# funcs.h comes from the upstream cfg files alone (no ROM). The real build gets
# it from the generator; the check build writes its own copy.
function(monoloco_check_funcs_header upstream out_dir)
    find_package(Python3 COMPONENTS Interpreter REQUIRED)
    file(MAKE_DIRECTORY "${out_dir}")
    execute_process(COMMAND "${Python3_EXECUTABLE}"
        "${upstream}/snesrecomp/tools/v2_sync_funcs_h.py"
        --cfg-dir "${upstream}/recomp" --out "${out_dir}/funcs.h"
        RESULT_VARIABLE result OUTPUT_QUIET)
    if(NOT result EQUAL 0)
        message(FATAL_ERROR "Cannot write funcs.h for ${upstream}")
    endif()
endfunction()

# monoloco_add_core(<game> [CHECK] SOURCES ... INCLUDES ... DEFINITIONS ...)
# CHECK: an object library without generated code, only to prove it compiles.
function(monoloco_add_core game)
    cmake_parse_arguments(CORE "CHECK" "" "SOURCES;INCLUDES;DEFINITIONS" ${ARGN})
    if(CORE_CHECK)
        set(target monoloco_game${game}_check)
        add_library(${target} OBJECT
            ${MONOLOCO_CORE_DIR}/core_common.c
            ${MONOLOCO_CORE_DIR}/game${game}.c
            ${CORE_SOURCES})
    else()
        set(target monoloco_game${game})
        add_library(${target} SHARED
            ${MONOLOCO_CORE_DIR}/core_common.c
            ${MONOLOCO_CORE_DIR}/game${game}.c
            ${CORE_SOURCES})
    endif()
    target_include_directories(${target} PRIVATE ${MONOLOCO_CORE_DIR} ${CORE_INCLUDES})
    target_compile_definitions(${target} PRIVATE
        MONOLOCO_GAME=${game}
        SNESRECOMP_TRACE=0
        SNESRECOMP_REVERSE_DEBUG=0
        SNESRECOMP_EXTERNAL_RAM_ROUTINE_GUARDS=1
        SYSTEM_VOLUME_MIXER_AVAILABLE=0
        ${CORE_DEFINITIONS})
    set_target_properties(${target} PROPERTIES
        C_STANDARD 11 C_EXTENSIONS ON
        C_VISIBILITY_PRESET hidden)
    # Upstream sources are built as their projects build them; only the
    # Monoloco glue is held to warnings.
    # Plain char is signed on the platforms upstream validated (x86-64, Apple
    # ARM64) but unsigned on Android ARM64.
    # -O3 and whole-program (Thin)LTO, as the upstream Release builds.
    target_compile_options(${target} PRIVATE -O3 -w -fsigned-char -fno-strict-aliasing
        $<$<NOT:$<BOOL:${CORE_CHECK}>>:-flto=thin>)
    set_source_files_properties(
        ${MONOLOCO_CORE_DIR}/core_common.c ${MONOLOCO_CORE_DIR}/game${game}.c
        PROPERTIES COMPILE_OPTIONS "-Wall;-Wextra;-Wno-unused-parameter")
    if(CORE_CHECK)
        message(STATUS "Monoloco: core ${game} compile check (no generated sources)")
        return()
    endif()
    target_link_options(${target} PRIVATE
        -O3 -flto=thin
        -Wl,--no-undefined
        -Wl,-Bsymbolic
        -Wl,--wrap=Die
        -Wl,--version-script=${MONOLOCO_CORE_DIR}/exports.map)
    target_link_libraries(${target} PRIVATE ${SNESRECOMP_RUNNER_LIBRARIES} m log)
    set(MONOLOCO_BUILT_CORES ${MONOLOCO_BUILT_CORES} ${target} CACHE INTERNAL "")
    message(STATUS "Monoloco: core ${game} enabled")
endfunction()

# Production switches for every runner.cmake include.
set(SNESRECOMP_ENABLE_TRACE OFF CACHE BOOL "" FORCE)
set(SNESRECOMP_ENABLE_MODS OFF CACHE BOOL "" FORCE)
set(SNESRECOMP_ENABLE_NET OFF CACHE BOOL "" FORCE)
set(SNES_COSIM OFF CACHE BOOL "" FORCE)
set(SNESRECOMP_ENABLE_FRAME_FINGERPRINTS OFF CACHE BOOL "" FORCE)
set(SNESRECOMP_ENABLE_PPU_DMA_HISTORY OFF CACHE BOOL "" FORCE)
set(SNESRECOMP_ENABLE_DISPATCH_HISTORY OFF CACHE BOOL "" FORCE)

# The desktop launcher, keybinding and crash-report pieces belong to the PC
# hosts; Android has its own (and each runner provides the host_report stubs).
function(monoloco_strip_desktop_sources list_var root)
    set(sources ${${list_var}})
    list(REMOVE_ITEM sources
        "${root}/runner/src/launcher.c"
        "${root}/runner/src/launcher_cache.c"
        "${root}/runner/src/launcher_picker.c"
        "${root}/runner/src/keybinds.c"
        "${root}/runner/src/host_report.c")
    set(${list_var} ${sources} PARENT_SCOPE)
endfunction()
