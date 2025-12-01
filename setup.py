"""
Setup script for building native C/C++/C# extensions
"""
from setuptools import setup, Extension
import numpy
import sys
import os

# Check if pybind11 is available
try:
    from pybind11.setup_helpers import Pybind11Extension, build_ext
    HAS_PYBIND11 = True
except ImportError:
    print("Warning: pybind11 not found - C++ extensions will be skipped")
    print("Install with: pip install pybind11")
    HAS_PYBIND11 = False

# Compiler flags
extra_compile_args = []
extra_link_args = []

if sys.platform == 'win32':
    # Windows MSVC
    extra_compile_args = ['/O2', '/arch:AVX2', '/openmp', '/std:c++17']
else:
    # Linux/Mac GCC/Clang
    extra_compile_args = ['-O3', '-march=native', '-mavx2', '-msse4.1', '-fopenmp', '-std=c++17']
    extra_link_args = ['-fopenmp']

# Image Fast Extension (C)
image_fast_ext = Extension(
    'image_fast',
    sources=['native/image_fast.c'],
    include_dirs=[numpy.get_include()],
    extra_compile_args=['/O2', '/arch:AVX2', '/openmp'] if sys.platform == 'win32' 
                       else ['-O3', '-march=native', '-mavx2', '-msse4.1', '-fopenmp'],
    extra_link_args=['-fopenmp'] if sys.platform != 'win32' else [],
)

# Database Fast Extension (C) - Phase 3
# Only build if sqlite3 is available
db_fast_ext = None
if sys.platform != 'win32':
    db_fast_ext = Extension(
        'db_fast',
        sources=['native/db_fast.c'],
        libraries=['sqlite3'],
        extra_compile_args=['-O3'],
    )

# Extensions list
ext_modules = [image_fast_ext]
if db_fast_ext:
    ext_modules.append(db_fast_ext)

# OCR Accelerator Extension (C++ with pybind11)
if HAS_PYBIND11:
    ocr_ext = Pybind11Extension(
        'ocr_accelerator',
        sources=['native/ocr_accelerator.cpp'],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        cxx_std=17,
    )
    ext_modules.append(ocr_ext)
    
    # Search Indexer Extension (C++ with pybind11) - Phase 4
    search_ext = Pybind11Extension(
        'search_indexer',
        sources=['native/search_indexer.cpp'],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        cxx_std=17,
    )
    ext_modules.append(search_ext)

setup(
    name='organisationsai-native',
    version='2.0.0',
    description='High-performance native extensions for OrganisationsAI',
    author='OrganisationsAI Team',
    ext_modules=ext_modules,
    cmdclass={'build_ext': build_ext} if HAS_PYBIND11 else {},
    install_requires=[
        'numpy>=1.20.0',
        'pybind11>=2.10.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: C',
        'Programming Language :: C++',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
