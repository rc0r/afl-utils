# afl-utils

Some utilities to automate crash analysis processing for crashes found with
american-fuzzy-lop.

#### afl-collect

afl-collect is a Python3 utility that copies all crash sample files from an afl
synchronisation directory used by multiple fuzzer instances when fuzzing in
parallel into a single location providing easy access for further crash
analysis.

Dependencies:

* Python3


Usage:  

    $ afl-collect.py [-h] [-f LIST_FILENAME] <afl-sync-dir> <collection-dir>
