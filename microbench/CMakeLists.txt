find_package(Qt6 6.2 REQUIRED COMPONENTS Core Gui Widgets Test)
set(CMAKE_AUTOMOC ON)

# Command line, statistics and report output shared by the benchmark
# executable and its tests.
add_library(microbench_support STATIC
    src/options.cpp
    src/options.h
    src/report.cpp
    src/report.h
    src/stats.cpp
    src/stats.h
)
target_include_directories(microbench_support PUBLIC src)
target_link_libraries(microbench_support PUBLIC Qt6::Core Qt6::Gui)

# Registers a Qt Test executable with CTest. Widgets are rendered through
# the offscreen platform so the tests run without a display.
function(microbench_add_test name)
    add_executable(${name} tests/${name}.cpp)
    target_link_libraries(${name} PRIVATE ${ARGN} Qt6::Test)
    add_test(NAME ${name} COMMAND ${name})
    set_tests_properties(${name} PROPERTIES ENVIRONMENT "QT_QPA_PLATFORM=offscreen")
endfunction()

microbench_add_test(test_support microbench_support)
