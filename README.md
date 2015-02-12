# afl-utils

Some utilities to automate crash analysis processing for crashes found with
american-fuzzy-lop.

#### afl-collect

afl-collect copies all crash sample files from an afl sync dir used by multiple
fuzzers when fuzzing in parallel into a single location providing easy access
for further crash analysis.

Usage: ´afl-collect.py <afl-sync-dir> <collection-dir>´
