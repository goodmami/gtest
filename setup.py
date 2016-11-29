#!/usr/bin/env python3

import os
from setuptools import setup

base_dir = os.path.dirname(__file__)
about = {}
with open(os.path.join(base_dir, "gtest", "__about__.py")) as f:
    exec(f.read(), about)

long_description = '''\
The gTest utility makes it easy to do regression testing, coverage
analysis, and semantic validation of DELPH-IN HPSG grammars.
'''

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__summary__'],
    long_description=long_description,
    url=about['__uri__'],
    author=about['__author__'],
    author_email=about['__email__'],
    license=about['__license__'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Utilities'
    ],
    keywords='hpsg delph-in grammar testing',
    packages=[
        'gtest'
    ],
    install_requires=[
        'pydelphin >=0.5.0'
    ],
    #entry_points={
    #    'console_scripts': [
    #        'gtest=gtest.main:main'
    #    ]
    #}
)
