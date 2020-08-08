#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from setuptools import setup, find_packages

PACKAGE_NAME = 'graven'

if 'darwin' in sys.platform or 'win' in sys.platform:
    err = "Refusing to install for platform `{}`, this tool requires a modern linux with losetup, etc"
    err = err.format(sys.platform)
    raise RunTimeError(err)

REQUIREMENTS = install_requires = [
    'pyparted==3.11.6', 'click',
    'pygments','termcolor', 'psutil',
    'coloredlogs'
]

setup(
    name=PACKAGE_NAME,
    version='0.1',
    author="elo",
    description="disk imaging utility",
    author_email='noreply@elo.enterprises',
    url='https://github.com/elo-enterprises/graven',
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    include_package_data=True,
    zip_safe=False,
    dependency_links=[
    ],
    entry_points={
        'console_scripts':
        [
            'graven = {0}.bin.graven:entry'.format(PACKAGE_NAME),
        ]},
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Programming Language :: Python :: 3",
    ],
)
