# afl-utils

afl-utils is a collection of utilities to assist fuzzing with
[american-fuzzy-lop (afl)](http://lcamtuf.coredump.cx/afl/).
afl-utils includes tools for:

* automated crash sample collection, verification, reduction and analysis (`afl-collect`, `afl-vcrash`)
* easy management of parallel (multi-core) fuzzing jobs (`afl-multicore`, `afl-multikill`)

In versions 1.03a and 1.04a multi-threading capabilities have been introduced to speed up things.
However if you observe some strange behaviour in one of these (or later) versions, please file a
bug report (either open an issue here on GH or send it in directly to `hlt99 at blinkenshell dot org`).
The latest non-multi-threading release that comes with all features is 1.02a. So if running the
multi-threaded version is somehow troubling for you, you can always `git checkout v1.02a` after cloning.
I might be adding a separate branch for multi-threaded afl-utils releases in the future.

### Dependencies

* Python3.4
* Python `sqlite3` package for database support
* `nohup` for `afl-multicore` normal mode (I'm using: 8.23 (GNU coreutils))
* `screen` for `afl-multicore` interactive/screen mode (I'm using: GNU Screen 4.02.01)
* `gdb` with Python support (for gdb script execution support)
* [Patched Exploitable](https://github.com/rc0r/exploitable) (for gdb script execution support)
* and of course you'll need [afl](http://lcamtuf.coredump.cx/afl/) for `afl-multicore`, `afl-multikill`

### Installation

The first thing to do is to install all required software packages if necessary. I'll
assume you've got Python 3 running and have got installed the other required tools.
Python package requirements should be automatically handled by the setup script
`setup.py` (see below).

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

    $ git checkout v1.04a

Next use `setup.py` to install the Python package system wide or in a virtual
environment. For a system wide install simply issue:

    $ python setup.py install

These utilities are in alpha development state so I **highly recommend** to use
a virtual environment instead:

    $ virtualenv venv
    $ source venv/bin/activate
    $ python setup.py install

If at any time something goes wrong, just remove the `venv` directory and start
all over with a fresh environment!

Now you're good to start:

    $ afl-collect --help


### The Tools

#### afl-collect

`afl-collect` basically copies all crash sample files from an afl synchronisation directory
(used by multiple afl instances when run in parallel) into a single location providing
easy access for further crash analysis. Beyond that `afl-collect` has some more advanced
features like invalid crash sample removing (see `afl-vcrash`) as well as generating and
executing `gdb` scripts that make use of [Exploitable](https://github.com/jfoote/exploitable).
The purpose of these scripts is to automate crash sample classification (see screenshot below)
and reduction.  
Version 1.01a introduced crash sample de-duplication using backtrace hashes calculated by
exploitable. To use this feature invoke `afl-collect` with `-e <gdb_script>` switch for
automatic gdb+exploitable script generation and execution. For each backtrace hash only a
single crash sample file will be kept.  
`afl-collect` is quite slow when operating on large sample sets and using gdb+exploitable
script execution, so be patient!  

Usage:

    afl-collect [-d DATABASE] [-e|-g GDB_EXPL_SCRIPT_FILE] [-f LIST_FILENAME]
                [-h] [-j THREADS] [-r] [-rr] sync_dir collection_dir target_cmd

    afl-collect copies all crash sample files from an afl sync dir used by multiple
    fuzzers when fuzzing in parallel into a single location providing easy access
    for further crash analysis.

    positional arguments:
      sync_dir              afl synchronisation directory crash samples will be
                            collected from.
      collection_dir        Output directory that will hold a copy of all crash
                            samples and other generated files. Existing files in the
                            collection directory will be overwritten!
      target_cmd            Path to the target binary and its command line arguments.
                            Use '@@' to specify crash sample input file position
                            (see afl-fuzz usage).

    optional arguments:
      -h, --help            show this help message and exit
      -d DATABASE_FILE, --database DATABASE_FILE
                            Submit classification data into a sqlite3 database.
                            Has no effect without '-e'.
      -e GDB_EXPL_SCRIPT_FILE, --execute-gdb-script GDB_EXPL_SCRIPT_FILE
                            Generate and execute a gdb+exploitable script after crash
                            sample collection for crash classification. (Like option
                            '-g', plus script execution.)
      -f LIST_FILENAME, --filelist LIST_FILENAME
                            Writes all collected crash sample filenames into a file
                            in the collection directory.
      -g GDB_SCRIPT_FILE, --generate-gdb-script GDB_SCRIPT_FILE
                            Generate gdb script to run 'exploitable.py' on all
                            collected crash samples. Generated script will be placed
                            into collection directory.
      -j NUM_THREADS, --threads NUM_THREADS
                            Enable parallel analysis by specifying the number of
                            threads afl-collect will utilize.
      -r, --remove-invalid  Verify collected crash samples and remove samples that
                            do not lead to crashes (runs 'afl-vcrash -qr' on collection
                            directory). This step is done prior to any script file or
                            file list generation/execution.
      -rr, --remove-unexploitable
                            Remove crash samples that have an exploitable
                            classification of 'NOT_EXPLOITABLE', 'PROBABLY_NOT_EXPLOITABLE'
                            or 'UNKNOWN'. Sample file removal will take place after
                            gdb+exploitable script execution. Has no effect without '-e'.


#### afl-multicore

`afl-multicore` starts several parallel fuzzing jobs in the background using `nohup` (Note:
So afl's fancy interface is gone). Fuzzer outputs (`stdout` and `stderr`) will be redirected
to `/dev/null`. Use `--verbose` to turn output redirection off. This is particularly useful
when debugging `afl-fuzz` invocations. The auto-generated file `nohup.out` might also contain
some useful info.  
If you want to check the fuzzers' progress see `fuzzer_stats` in the respective fuzzer
directory in the synchronisation dir (`sync_dir/SESSION###/fuzzer_stats`)! The master instance
files are always located at `sync_dir/SESSION000/`.  
An `afl-multicore` session can (and should!) easily be aborted with the help of
`afl-multikill` (see below).  
If you prefer to work with afl's UI instead of background processes and stat files, screen
mode is for you. "Interactive" screen mode can be enabled using the `-i` switch. In order to
use it, start `afl-multicore` from **inside** a `screen` session. A new screen window is created
for every afl instance. Though screen mode is not supported by `afl-multikill`.  
**Attention:** When using screen mode be sure to set necessary environment variables using the
`--env-vars` parameter of `afl-multicore`! Alternatively run `screen -X setenv <var_name> <var_value>`
 from inside `screen` before running `afl-multicore`. Both ways the environment is inherited
 by all subsequently created screen windows.

**Tip:** `afl-multicore` can be used to resume a parallel fuzzing session. Just provide "-" as
input dir and leave all other parameters as in the initiating invocation of the fuzzing session.

Usage:

    afl-multicore [-h] [-a afl_args] [-e env_vars] [-i] [-j SLAVE_NUMBER]
                  [-S SESSION] [-s] [-v] input_dir sync_dir target_cmd

    afl-multicore starts several parallel fuzzing jobs, that are run in the
    background. For fuzzer stats see 'sync_dir/SESSION###/fuzzer_stats'!

    positional arguments:
      input_dir             Input directory that holds the initial test cases
                            (afl-fuzz's -i option).
      sync_dir              afl synchronisation directory that will hold fuzzer
                            output files (afl-fuzz's -o option).
      target_cmd            Path to the target binary and its command line
                            arguments. Use '@@' to specify crash sample input
                            file position (see afl-fuzz usage).

    optional arguments:
      -h, --help            show this help message and exit
      -a AFL_ARGS, --afl-args AFL_ARGS
                            afl-fuzz specific parameters. Enclose in quotes, -i
                            and -o must not be specified!
      -e ENV_VARS, --env-vars ENV_VARS
                            (Screen mode only) Comma separated list of environment
                            variable names and values for newly created screen
                            windows. Enclose in quotes! Example: --env-vars
                            "AFL_PERSISTENT=1,LD_PRELOAD=/path/to/yourlib.so"
      -i, --screen          Interactive screen mode. Starts every afl instance
                            in a separate screen window. Run from inside screen
                            (Default: off)!
      -j SLAVE_NUMBER, --slave-number SLAVE_NUMBER
                            Number of slave instances to run (Default: 3).
      -S SESSION, --session SESSION
                            Provide a name for the fuzzing session. Master
                            outputs will be written to 'sync_dir/SESSION000'
                            (Default='SESSION').
      -s, --slave-only      Slave-only mode, do not start a master instance
                            (Default: off).
      -v, --verbose         For debugging purposes do not redirect stderr and
                            stdout of the created subprocesses to /dev/null
                            (Default: off). Check 'nohup.out' for further outputs.


#### afl-multikill

Aborts all `afl-fuzz` instances belonging to an active non-interactive `afl-multicore`
session. `afl-multicore` sessions that were started in `screen` mode can not be aborted!

Usage:

    afl-multikill [-S SESSION]

    afl-multikill aborts all afl-fuzz instances belonging to an active
    afl-multicore session. Interactive screen sessions are not supported!

    optional arguments:
      -h, --help            show this help message and exit
      -S SESSION, --session SESSION
                            afl-multicore session to abort
                            (Default='SESSION').


#### afl-vcrash

`afl-vcrash` verifies that afl-fuzz crash samples really lead to crashes in the target
binary and optionally removes these samples automatically.  
Note: `afl-vcrash` functionality is incorporated into `afl-collect`. If `afl-collect` is
invoked with switch `-r`, it runs `afl-vcrash -qr` to quietly remove invalid samples from
the collected files.  
To enable parallel crash sample verification provide `-j` followed by the desired number
of threads `afl-vcrash` will utilize. Depending on the target process you're fuzzing,
running multiple threads in parallel can significantly improve verification speeds.

Usage:

    afl-vcrash [-f LIST_FILENAME] [-h] [-j THREADS] [-q] [-r] collection_dir
               target_command [target_command_args]

    afl-vcrash verifies that afl-fuzz crash samples lead to crashes in the
    target binary.

    positional arguments:
      collection_dir        Directory holding all crash samples that will
                            be verified.
      target_command        Target binary including command line options.
                            Use '@@' to specify crash sample input file
                            position (see afl-fuzz usage).

    optional arguments:
      -h, --help            show this help message and exit
      -f LIST_FILENAME, --filelist LIST_FILENAME
                            Writes all crash sample file names that do not
                            lead to crashes into a file.
      -j NUM_THREADS, --threads NUM_THREADS
                            Enable parallel verification by specifying the
                            number of threads afl-vcrash will utilize.
      -q, --quiet           Suppress output of crash sample file names that
                            do not lead to crashes. This is particularly
                            useful when combined with '-r' or '-f'.
      -r, --remove          Remove crash samples that do not lead to crashes.


  
### Problems

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

### Feature Ideas / ToDo / Contribution

If you're missing some feature in afl-utils or like to propose some changes, I'd appreciate
your contributions. Just send your bug reports, feature ideas, code patches or pull requests
either via Github or directly to `hlt99 at blinkenshell dot org`!

- [x] submit classification data into some sort of database
    - [x] basic sqlite3 database support added
    - [ ] want more db connectors? Drop me a line!
- [x] afl-multicore: wrapper script that starts multiple afl-instances for parallel fuzzing on multiple cores
    - [x] screen mode
    - [ ] tmux mode (only, if requested explicitly)
    - [ ] afl-multicore_watch/afl-multiplot for checking fuzzer_stats (might get contributed by [@arisada](https://github.com/arisada)?)
- [ ] We're growing larger, do we need unit tests?


### Screenshots

#### afl-collect

Usage:  

![afl-collect_usage](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_collect_usage.png)

Sample output:

![afl-collect_sample](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_collect_sample.png)

#### afl-multicore

Usage (normal mode):  

![afl-multicore_usage](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_multicore_usage.png)

Sample output (normal mode):

![afl-multicore_sample](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_multicore_sample.png)


#### afl-vcrash

Usage:

![afl-vcrash_usage](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_vcrash_usage.png)
