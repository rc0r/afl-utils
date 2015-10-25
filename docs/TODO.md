# Feature Ideas / ToDo / Contribution

If you're missing some feature in afl-utils or like to propose some changes, I'd appreciate
your contributions. Just send your bug reports, feature ideas, code patches or pull requests
either via Github or directly to `hlt99 at blinkenshell dot org`!

- [x] submit classification data into some sort of database
    - [x] basic sqlite3 database support added
    - [ ] want more db connectors? Drop me a line!
- [x] afl-multicore: wrapper script that starts multiple afl-instances for parallel fuzzing on multiple cores
    - [x] screen mode
    - [ ] tmux mode (only, if requested explicitly)
    - [x] afl-stats for checking fuzzer_stats


# Problems

* `afl-vcrash` might miss *some* invalid crash samples. Identification of real crashes is
  hard and needs improvements!
* `afl-vcrash` identifies *some* crash samples as invalid that are considered valid by
  `afl-fuzz` when run with option `-C`.
* Tool outputs might get cluttered if core dumps/kernel crash/libc messages are displayed on
  your terminal (see `man core(5)`; workaround anybody?).
  **Hint:** Redirect `stdout` of `afl-collect`/`afl-vcrash` to some file to afterwards check
  their outputs!
* ~~gdb+exploitable script execution will be interrupted when using samples that do not lead
  to actual crashes. `afl-collect` will print the files name causing the trouble (for manual
  removal).~~ Fixed by using a patched `exploitable.py` that handles `NoThreadRunningError`
  (see [Exploitable](https://github.com/rc0r/exploitable)). **Be sure to use the patched
  version of `exploitable.py`!**

