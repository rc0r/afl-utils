"""
Copyright 2015-2016 @_rc0r <hlt99@blinkenshell.org>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from setuptools import setup
from setuptools import find_packages

import afl_utils

dependencies = [
    'exploitable==1.32-rcor',       # needed for gdb script execution
    'simplejson',                   # needed for config files
    'twitter',                      # needed for afl-stats (twitter access)
]

dependency_links = [
    'https://github.com/rc0r/exploitable/tarball/experimental#egg=exploitable-1.32-rcor'
]

afl_scripts = [
    'afl-collect',
    'afl-cron',
    'afl-minimize',
    'afl-multicore',
    'afl-multikill',
    'afl-stats',
    'afl-sync',
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
    test_suite='tests'
)
