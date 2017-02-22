#!/usr/bin/env python2.7
# encoding:utf-8
# Created on 2017-02-21, by dozysun

from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("dsencrypt.py")
)