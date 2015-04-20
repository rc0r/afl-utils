# afl-utils

afl-utils is a collection of utilities to assist fuzzing with
[american-fuzzy-lop (afl)](http://lcamtuf.coredump.cx/afl/).
afl-utils includes tools for:

* automated crash sample collection, verification, reduction and analysis (`afl_collect`, `afl_vcrash`)
* easy management of parallel (multi-core) fuzzing jobs (`afl_multicore`, `afl_multikill`)

### Dependencies

* Python3
* Python `sqlite3` package for database support
* `nohup` for `afl_multicore` normal mode (I'm using: 8.23 (GNU coreutils))
* `screen` for `afl_multicore` interactive/screen mode (I'm using: GNU Screen 4.02.01)
* `gdb` with Python support (for gdb script execution support)
* [Patched Exploitable](https://github.com/rc0r/exploitable) (for gdb script execution support)

### Installation

The first thing to do is to install all required software packages if necessary. I'll
assume you've got Python 3 running (with `sqlite3` packages installed; PyPi is your
friend) and have installed the other required tools.

#### Set up exploitable

In order to use advanced afl-utils features exploitable needs to be installed and
set up to work with `gdb`.

Get the patched version from GH:  

    $ git clone https://github.com/rc0r/exploitable

Next install exploitable globally or locally according to the instructions in the
`Usage` section of exploitables' `README.md`!

#### afl-utils Installation

Now get `afl-utils` from the GH repo:

    $ git clone https://github.com/rc0r/afl-utils
    
If you want to stick with the latest development version you're good to go. If you
prefer to use a release version, run:

    $ cd afl-utils
    $ git checkout <release_version>

For example:

    $ git checkout v1.01a

If necessary make the afl-utils scripts in the root dir executable! Now you're
good to start:

    $ ./afl_collect --help


### The Tools

#### afl\_collect

`afl_collect` basically copies all crash sample files from an afl synchronisation directory
(used by multiple afl instances when run in parallel) into a single location providing
easy access for further crash analysis. Beyond that `afl_collect` has some more advanced
features like invalid crash sample removing (see `afl_vcrash`) as well as generating and
executing `gdb` scripts that make use of [Exploitable](https://github.com/jfoote/exploitable).
The purpose of these scripts is to automate crash sample classification (see screenshot below)
and reduction. Version 1.01a introduced crash sample de-duplication using backtrace hashes
calculated by exploitable. To use this feature invoke `afl_collect` with `-e <gdb_script>`
switch for automatic gdb+exploitable script generation and execution. For each backtrace hash
only a single crash sample file will be kept.  

Usage:  

![afl_collect_usage](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_collect_usage.png)

Sample output:

![afl_collect_sample](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_collect_sample.png)


#### afl\_multicore

`afl_multicore` starts several parallel fuzzing jobs in the background using `nohup` (Note:
So afl's fancy interface is gone). Fuzzer outputs (`stdout` and `stderr`) will be redirected
to `/dev/null`. Use `--verbose` to turn output redirection off. This is particularly useful
when debugging `afl-fuzz` invocations. The auto-generated file `nohup.out` might also contain
some useful info.  
If you want to check the fuzzers' progress see `fuzzer_stats` in the respective fuzzer
directory in the synchronisation dir (`sync_dir/SESSION###/fuzzer_stats`)! The master instance
files are always located at `sync_dir/SESSION000/`.  
An `afl_multicore` session can (and should!) easily be aborted with the help of
`afl_multikill` (see below).  
If you prefer to work with afl's UI instead of background processes and stat files, screen
mode is for you. "Interactive" screen mode can be enabled using the `-i` switch. In order to
use it, start `afl_multicore` from **inside** a `screen` session. A new screen window is created
for every afl instance. Though screen mode is not supported by `afl_multikill`.

Usage (normal mode):  

![afl_multicore_usage](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_multicore_usage.png)

Sample output (normal mode):

![afl_multicore_sample](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_multicore_sample.png)


#### afl\_multikill

Aborts all `afl-fuzz` instances belonging to an active non-interactive `afl_multicore`
session. `afl_multicore` sessions that were started in `screen` mode can not be aborted!

Usage:

    $ afl_multikill [-S SESSION]
        

#### afl\_vcrash

`afl_vcrash` verifies that afl-fuzz crash samples really lead to crashes in the target
binary and optionally removes these samples automatically.  
Note: `afl_vcrash` functionality is incorporated into `afl_collect`. If `afl_collect` is
invoked with switch `-r`, it runs `afl_vcrash -qr` to quietly remove invalid samples from
the collected files.

Usage:

![afl_vcrash_usage](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_vcrash_usage.png)

  
### Problems

* `afl_collect` is quite slow (especially when operating on large sample sets and using
   gdb+exploitable script execution), so be patient!
* `afl_vcrash` might miss *some* invalid crash samples. Identification of real crashes is
  hard and needs improvements!
* `afl_vcrash` identifies *some* crash samples as invalid that are considered valid by
  `afl-fuzz` when run with option `-C`.
* Tool outputs might get cluttered if core dumps/kernel crash messages are displayed on
  your terminal (see `man core(5)`; workaround anybody?).
* ~~gdb+exploitable script execution will be interrupted when using samples that do not lead
  to actual crashes. `afl_collect` will print the files name causing the trouble (for manual
  removal).~~ Fixed by using a patched `exploitable.py` that handles `NoThreadRunningError`
  (see [Exploitable](https://github.com/rc0r/exploitable)). **Be sure to use the patched
  version of `exploitable.py`!**

### Feature Ideas / ToDo

- [x] submit classification data into some sort of database
    - [x] basic sqlite3 database support added
    - [ ] want more db connectors? Drop me a line!
- [ ] auto clean-up of uninteresting crashes
    - [x] by exploitable classification
    - [x] de-duping by exploitable backtrace hashes
    - [ ] through other means of de-duplicating crash samples (might be clever to
          incorporate this into the crash collection step;
          [some ideas](https://groups.google.com/forum/#!topic/afl-users/b5v3mY_hy30))
- [x] afl_multicore: wrapper script that starts multiple afl-instances for parallel fuzzing on multiple cores
    - [x] screen mode
    - [ ] tmux mode (only, if requested explicitly)
    - [ ] afl_multicore_watch for checking fuzzer_stats (contribution by [@arisada](https://github.com/arisada))?
- [ ] afl_resume: wrapper script that resumes multiple afl-instances at once (resume an `afl_multicore` session)
- [ ] speed improvements for `afl_collect`
