#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Setup file for stealthdemo.

    This file was generated with PyScaffold 2.5.7, a tool that easily
    puts up a scaffold for your new Python project. Learn more under:
    http://pyscaffold.readthedocs.org/
"""

import sys
from setuptools import setup, find_packages
import stealthdemo

requires = []

def setup_package():
    setup(
        name='cloudci',
        version=stealthdemo.__version__,
        description='The command line tool for cloud automation',
        url='https://bitbucket.org/duyuyang/stealthdemo',
        author='Du Yuyang',
        author_email='du.r.yuyang@gmail.com',
        scripts=['bin/cloudci'],
        install_requires=requires,
        packages=find_packages(exclude=['tests*']),
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Natural Language :: English',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    )


if __name__ == "__main__":
    setup_package()
