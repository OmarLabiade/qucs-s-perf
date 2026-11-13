cmake_minimum_required(VERSION 3.21)
project(qucs-s-perf LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE RelWithDebInfo)
endif()

# Same unwinding setup as the instrumented Qucs-S build, so that perf and
# Hotspot give readable stacks for the microbench too.
add_compile_options(-Wall -Wextra -Wpedantic -fno-omit-frame-pointer)

enable_testing()
add_subdirectory(microbench)
