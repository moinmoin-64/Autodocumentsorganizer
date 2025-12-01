"""
Setup script for building native C/C++/C# extensions
"""
from setuptools import setup, Extension
import numpy
import sys
import os

# Compiler flags
extra_compile_args = []
extra_link_args = []

if sys.platform == 'win32':
    # Windows MSVC
    extra_compile_args = ['/O2', '/arch:AVX2', '/openmp']
else:
    # Linux/Mac GCC/Clang
    extra_compile_args = ['-O3', '-march=native', '-mavx2', '-msse4.1', '-fopenmp']
    extra_link_args = ['-fopenmp']

# Image Fast Extension (C)
image_fast_ext = Extension(
    'image_fast',
    sources=['native/image_fast.c'],
    include_dirs=[numpy.get_include()],
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
)

setup(
    name='organisationsai-native',
    version='1.0.0',
    description='High-performance native extensions for OrganisationsAI',
    author='OrganisationsAI Team',
    ext_modules=[image_fast_ext],
    install_requires=[
        'numpy>=1.20.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: C',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
