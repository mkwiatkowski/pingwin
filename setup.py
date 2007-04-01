#!/usr/bin/env python2.5
import os
from setuptools import setup

setup(name = 'pingwin',
      version = '0.1',
      url = "http://code.google.com/p/pingwin/",

      packages = ['pingwin'],
      entry_points = { 'console_scripts': [ 'pingwin = pingwin.client:run',
                                            'pingwin_server = pingwin.server:run' ]},

      install_requires = ['pygame', 'Twisted'],

      # We use nose for testing.
      test_suite = 'nose.collector',
      tests_require = ['nose', 'pinocchio'])

# Instruct nose to run doctests.
os.environ['NOSE_WITH_DOCTEST'] = 'True'
os.environ['NOSE_DOCTEST_TESTS'] = 'True'
