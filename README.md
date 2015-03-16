# afl-utils

Some utilities to automate crash sample processing and analysis for crashes
found with [american-fuzzy-lop (afl)](http://lcamtuf.coredump.cx/afl/).

### Dependencies

* Python3 (with sqlite3)
* [Exploitable](https://github.com/rc0r/exploitable) (for script execution support)

### Problems / Bugs

* These tools are slow!
* `avl_vcrash` might miss *some* invalid crash samples. Identification of real crashes is
  hard and needs improvements!
* `avl_vcrash` identifies *some* crash samples as invalid that are considered valid by
  `afl-fuzz` when run with option `-C`.
* Tool outputs might get cluttered if core dumps/kernel crash messages are displayed on
  your terminal (see `man core(5)`; workaround anybody?).
* ~~gdb+exploitable script execution will be interrupted when using samples that do not lead
  to actual crashes. `afl_collect` will print the files name causing the trouble (for manual
  removal).~~ Fixed by using a patched `exploitable.py` that handles `NoThreadRunningError`
  (see [Exploitable](https://github.com/rc0r/exploitable)). **Be sure to use the patched
  version of `exploitable.py`!**
* The more advanced features like gdb+exploitable script generation and execution as well as
  crash sample verification *probably will* fail for targets that don't read their input from
  files (`afl-fuzz` invoked without `-f <filename>`) but from `stdin`. I didn't look into this
  yet.

### Feature Ideas / ToDo

- [ ] "`stdin`-support" (see Problems/Bugs); We do get crash samples for "`stdin`"-mode, right?!
- [x] submit classification data into some sort of database
    - [x] basic sqlite3 database support added
- [ ] auto clean-up of uninteresting crashes
    - [x] by exploitable classification
    - [ ] through some means of deduplicating crash samples (might be clever to incorporate this into
          the crash collection step;
          [some ideas](https://groups.google.com/forum/#!topic/afl-users/b5v3mY_hy30))

### The Tools

#### afl\_collect

`afl_collect` basically copies all crash sample files from an afl synchronisation directory
(used by multiple afl instances when run in parallel) into a single location providing
easy access for further crash analysis. Beyond that `afl_collect` has some more advanced
features like invalid crash sample removing as well as generating and executing `gdb` scripts
that make use of [Exploitable](https://github.com/jfoote/exploitable). The purpose of these
scripts is to automate crash sample classification (see screenshot below).  

Usage:  

![afl_collect_usage](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_collect_usage.png)

Sample output:

![afl_collect_sample](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_collect_sample.png)

#### afl\_vcrash

afl\_vcrash verifies that afl-fuzz crash samples lead to crashes in the target binary and
optionally removes these samples automatically.

Usage:

![afl_vcrash_usage](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_vcrash_usage.png)
  
### Changelog

Release | Description
:-------:|----
0.10a | Initial release, just collect crash sample files
0.11a | Crash sample file list creation added, afl_vcrash added
0.12a | gdb+exploitable script generation added
0.13a | Auto-cleanup of invalid crash samples added
0.14a | gdb+exploitable script execution and output parsing added for easy crash classification
0.15a | Code refactoring, minor bug fixes
0.16a | Minor bug fix for gdb+exploitable script generation
0.17a | Basic SQLite3 database support added
0.18a | Fixed gdb+exploitable script interruptions that occur on graceful exits of the target binary
0.19a | Added auto-cleanup feature for samples leading to uninteresting crashes