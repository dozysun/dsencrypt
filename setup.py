#!/usr/bin/env python2.7
# encoding:utf-8
# Created on 2017-02-21, by dozysun

from distutils.core import setup, Extension

dsencpryt_module = Extension('dsencrypt', sources=['dsencrypt.c'],)

setup(
      name='dsencrypt',
      version='0.1',
      description='simple encrypt module',
      ext_modules=[dsencpryt_module]
)
