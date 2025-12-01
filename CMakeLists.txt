# CMakeLists.txt for Native C/C++ Extensions
cmake_minimum_required(VERSION 3.15)
project(OrganisationsAI_Native)

# C++17 Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Python
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

# Optimization flags
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=native -fopenmp")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")
elseif(MSVC)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /O2 /arch:AVX2 /openmp")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W3")
endif()

# OCR Accelerator (C++ with pybind11)
pybind11_add_module(ocr_accelerator native/ocr_accelerator.cpp)
target_compile_options(ocr_accelerator PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang>:-O3 -march=native -fopenmp>
    $<$<CXX_COMPILER_ID:MSVC>:/O2 /arch:AVX2 /openmp>
)

# Optional: Link Intel TBB for better parallelism
find_package(TBB QUIET)
if(TBB_FOUND)
    target_link_libraries(ocr_accelerator PRIVATE TBB::tbb)
    target_compile_definitions(ocr_accelerator PRIVATE HAS_TBB)
endif()

# Installation
install(TARGETS ocr_accelerator LIBRARY DESTINATION .)
