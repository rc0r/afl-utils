# Troubleshooting

There are some known issues and quirks that arise when working with afl-utils. Check out the
following list to get advice on how to workaround these issues!

* `afl-vcrash` might miss *some* invalid crash samples. Identification of real crashes is
  hard and needs improvements!
* Tool outputs might get cluttered if core dumps/kernel crash/libc messages are displayed on
  your terminal (see `man core(5)`; workaround anybody?).
  **Hint:** Redirect `stdout` of `afl-collect`/`afl-vcrash` to some file to afterwards check
  their outputs!
* ~~gdb+exploitable script execution will be interrupted when using samples that do not lead
  to actual crashes. `afl-collect` will print the files name causing the trouble (for manual
  removal).~~ Fixed by using a patched `exploitable.py` that handles `NoThreadRunningError`
  (see [Exploitable](https://github.com/rc0r/exploitable)). **Be sure to use the patched
  version of `exploitable.py`!**

Please report other issues via the bug tracker at the
[Github Issues](https://github.com/rc0r/afl-utils/issues) page! If you happen to have a better
solution to one of these problems you're kindly asked to share it as well (as a comment to an
existing issue or just drop me a line on Twitter/via mail)!

