# afl-utils

Some utilities to automate crash analysis processing for crashes found with
american-fuzzy-lop (afl).

#### Dependencies

* Python3

#### afl-collect

afl-collect is a Python3 utility that copies all crash sample files from an afl
synchronisation directory used by multiple fuzzer instances when fuzzing in
parallel into a single location providing easy access for further crash
analysis.

Usage:  

    $ afl-collect.py [-h] [-f LIST_FILENAME] sync_dir collection_dir

Run `afl-collect.py -h` for more detailed usage information.

#### afl-vcrash

afl-vcrash verifies that afl-fuzz crash samples lead to crashes in the target
binary.

Usage:

    $ afl-vcrash.py [-h] [-f LIST_FILENAME] [-q] [-r] collection_dir -- target_command

Run `afl-vcrash.py -h` for more detailed usage information.  
  
Caveats:  

* Might miss *some* invalid crash samples. Identification of real crashes is
  hard and needs improvements!
* Identifies *some* crash samples as invalid that are considered valid by
  `afl-fuzz` when run with option `-C`.
* Tool output might get cluttered if kernel crash messages are displayed on
  your terminal.