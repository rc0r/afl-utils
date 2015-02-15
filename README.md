# afl-utils

Some utilities to automate crash sample processing and analysis for crashes
found with [american-fuzzy-lop (afl)](http://lcamtuf.coredump.cx/afl/).

#### Dependencies

* Python3
* [Exploitable](https://github.com/jfoote/exploitable) (for script execution support)

#### Problems / Bugs

* `avl_vcrash` might miss *some* invalid crash samples. Identification of real crashes is
  hard and needs improvements!
* `avl_vcrash` identifies *some* crash samples as invalid that are considered valid by
  `afl-fuzz` when run with option `-C`.
* Tool outputs might get cluttered if core dumps/kernel crash messages are displayed on
  your terminal.


#### afl\_collect

afl\_collect is a Python3 utility that copies all crash sample files from an afl
synchronisation directory into a single location providing easy access for
further crash analysis. The afl synchronisation directory is created when using
multiple fuzzer instances in parallel.  

Usage:  

![afl_collect_usage](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_collect_usage.png)

Sample output:

![afl_collect_sample](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_collect_sample.png)

#### afl\_vcrash

afl\_vcrash verifies that afl-fuzz crash samples lead to crashes in the target
binary.

Usage:

![afl_vcrash_usage](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_vcrash_usage.png)
  
