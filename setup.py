from distutils.core import setup
from setuptools import find_packages

import afl_utils

dependencies = [
    'twitter',
]

dependency_links = [
]

afl_scripts = [
    'afl-collect',
    'afl-minimize',
    'afl-multicore',
    'afl-multikill',
    'afl-stats',
    'afl-vcrash'
]

setup(
    name='afl-utils',
    version=afl_utils.__version__,
    packages=find_packages(),
    url='https://github.com/rc0r/afl-utils',
    license='Apache License 2.0',
    author=afl_utils.__author_name__,
    author_email=afl_utils.__author_email__,
    description='Utilities for automated crash sample processing/analysis, easy afl-fuzz job management and corpus '
                'optimization',
    install_requires=dependencies,
    dependency_links=dependency_links,
    platforms=[
        'Any',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.4',
        'Topic :: Fuzzing Utilities',
    ],
    scripts=afl_scripts,
    keywords=[
        'Fuzzing',
        'American Fuzzy Lop',
    ],
)
