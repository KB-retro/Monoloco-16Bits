# Game 2: mirrors upstream/game2's dkc2_snesrecomp_headless target, including
# its configure-time PPU copy (cmake/ProjectKongsPpu.cmake) and the two scripts
# that adapt the generated sources.
set(UPSTREAM ${MONOLOCO_UPSTREAM}/game2)
monoloco_generated_sources(2 GENERATED)
if(NOT GENERATED AND NOT MONOLOCO_CHECK_CORES)
    message(STATUS "Monoloco: no generated sources for game 2; core skipped")
    return()
endif()
set(SNESRECOMP_ROOT ${UPSTREAM}/snesrecomp)
include(${SNESRECOMP_ROOT}/runner/runner.cmake)

# Same patch as ProjectKongsPpu.cmake, which assumes its own source directory.
set(_ppu_source "${SNESRECOMP_ROOT}/runner/src/snes/ppu.c")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${_ppu_source}")
file(READ "${_ppu_source}" _ppu)
function(game2_ppu_patch before after)
    string(FIND "${_ppu}" "${before}" match)
    if(match EQUAL -1)
        message(FATAL_ERROR "Game 2 PPU integration needs review: missing anchor ${before}")
    endif()
    string(LENGTH "${before}" anchor_length)
    math(EXPR after_anchor "${match} + ${anchor_length}")
    string(SUBSTRING "${_ppu}" ${after_anchor} -1 remainder)
    string(FIND "${remainder}" "${before}" duplicate)
    if(NOT duplicate EQUAL -1)
        message(FATAL_ERROR "Game 2 PPU integration has an ambiguous anchor")
    endif()
    string(REPLACE "${before}" "${after}" _patched "${_ppu}")
    set(_ppu "${_patched}" PARENT_SCOPE)
endfunction()
game2_ppu_patch("#include \"ppu.h\""
    "#include \"ppu.h\"\n#include \"dkc2_kongs.h\"")
game2_ppu_patch("if(row < spriteHeight) {"
    "int kongVisible = Dkc2KongsOamVisible(line, index >> 1);\n    if(kongVisible > 0 || (kongVisible < 0 && row < spriteHeight)) {")
game2_ppu_patch("if(x + spriteSize > -left_extra) {"
    "if(kongVisible > 0 || x + spriteSize > -left_extra) {")
game2_ppu_patch("index = foundSprites[i - 1];"
    "index = foundSprites[i - 1];\n    if (Dkc2KongsRenderOam(ppu, line, index >> 1)) { tilesFound++; continue; }")
set(_ppu_output "${CMAKE_CURRENT_BINARY_DIR}/dkc2_ppu.c")
file(WRITE "${_ppu_output}.in" "${_ppu}")
configure_file("${_ppu_output}.in" "${_ppu_output}" COPYONLY)
list(REMOVE_ITEM SNESRECOMP_RUNNER_SOURCES "${_ppu_source}")
list(APPEND SNESRECOMP_RUNNER_SOURCES "${_ppu_output}")

# Both scripts adapt the generated sources in place, as upstream's configure does.
set(_GEN_SCRIPTS)
if(GENERATED)
    set(_GEN_SCRIPTS apply_dkc2_kongs_overrides.py apply_dkc2_music_overrides.py)
endif()
find_package(Python3 COMPONENTS Interpreter REQUIRED)
foreach(script IN ITEMS ${_GEN_SCRIPTS})
    execute_process(COMMAND "${Python3_EXECUTABLE}" "${UPSTREAM}/scripts/${script}"
        --generated-dir "${MONOLOCO_GAME2_GEN_DIR}"
        RESULT_VARIABLE result OUTPUT_QUIET)
    if(NOT result EQUAL 0)
        message(FATAL_ERROR "Game 2: ${script} failed on the generated sources")
    endif()
endforeach()

monoloco_strip_desktop_sources(SNESRECOMP_RUNNER_SOURCES ${SNESRECOMP_ROOT})
set(RUNNER
    dkc2_kongs.c dkc2_music.c dkc2_msu1.c dkc2_spc_music.c
    dkc2_game.c dkc2_coop.c dkc2_video.c dkc2_hdma.c
    headless_host.c input_playback.c verified_rom.c)
list(TRANSFORM RUNNER PREPEND ${UPSTREAM}/runner/)
set(INCLUDES ${UPSTREAM}/runner ${UPSTREAM}/recomp ${SNESRECOMP_RUNNER_INCLUDE_DIRS})
if(GENERATED)
    monoloco_add_core(2 SOURCES ${SNESRECOMP_RUNNER_SOURCES} ${GENERATED} ${RUNNER}
        INCLUDES ${INCLUDES})
else()
    monoloco_check_funcs_header(${UPSTREAM} ${CMAKE_CURRENT_BINARY_DIR}/check)
    monoloco_add_core(2 CHECK SOURCES ${SNESRECOMP_RUNNER_SOURCES} ${RUNNER}
        INCLUDES ${CMAKE_CURRENT_BINARY_DIR}/check ${INCLUDES})
endif()
