cmake_minimum_required(VERSION 3.20)

project(SnakeLinkedListClient
    VERSION 0.1.0
    LANGUAGES C CXX
)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")

include(FetchContent)

set(CMAKE_POLICY_VERSION_MINIMUM 3.5 CACHE STRING "" FORCE)

set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(BUILD_GAMES OFF CACHE BOOL "" FORCE)
set(BUILD_TESTING ON CACHE BOOL "" FORCE)

FetchContent_Declare(
    raylib
    URL https://github.com/raysan5/raylib/archive/refs/tags/5.5.tar.gz
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_MakeAvailable(raylib)

add_library(snake_core STATIC
    src/app_ui.c
    src/game_core.c
    src/high_score.c
    src/snake_list.c
)
target_include_directories(snake_core PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)
if (MSVC)
    target_compile_options(snake_core PRIVATE /W4)
else()
    target_compile_options(snake_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_executable(snake_client
    src/main.c
)
target_include_directories(snake_client PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)
target_link_libraries(snake_client PRIVATE snake_core raylib)

if (MSVC)
    target_compile_options(snake_client PRIVATE /W4)
else()
    target_compile_options(snake_client PRIVATE -Wall -Wextra -Wpedantic)
endif()

enable_testing()

set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
set(gtest_disable_pthreads ON CACHE BOOL "" FORCE)
FetchContent_Declare(
    googletest
    URL https://github.com/google/googletest/archive/refs/tags/release-1.10.0.zip
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_MakeAvailable(googletest)

add_executable(snake_tests
    tests/app_ui_test.cpp
    tests/game_core_test.cpp
    tests/high_score_test.cpp
    tests/snake_list_test.cpp
    tests/smoke_test.cpp
)
target_include_directories(snake_tests PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)
if (TARGET GTest::gtest_main)
    target_link_libraries(snake_tests PRIVATE snake_core GTest::gtest_main)
else()
    target_link_libraries(snake_tests PRIVATE snake_core gtest_main)
endif()

include(GoogleTest)
gtest_discover_tests(snake_tests)
