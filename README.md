# afl-utils

afl-utils is a collection of utilities to assist fuzzing with
[american-fuzzy-lop (afl)](http://lcamtuf.coredump.cx/afl/).
afl-utils includes tools for:

* automated crash sample collection, verification, reduction and analysis (`afl-collect`, `afl-vcrash`)
* easy management of parallel (multi-core) fuzzing jobs (`afl-multicore`, `afl-multikill`)

![afl-collect_sample](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_collect_sample.png)

**For installation instructions see [docs/INSTALL.md](https://github.com/rc0r/afl-utils/blob/master/docs/INSTALL.md).**

In versions 1.03a and 1.04a multi-threading capabilities have been introduced to speed up things.
However if you observe some strange behaviour in one of these (or later) versions, please file a
bug report (either open an issue here on GH or send it in directly to `hlt99 at blinkenshell dot org`).
The latest non-multi-threading release that comes with all features is 1.02a. So if running the
multi-threaded version is somehow troubling for you, you can always `git checkout v1.02a` after cloning.
I might be adding a separate branch for multi-threaded afl-utils releases in the future.


## afl-collect

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


## afl-minimize

Helps to create a minimized corpus from samples of a parallel fuzzing job. It
basically works as follows:

1. Collect all queue samples from an afl synchronisation directory in `collection_dir`.
2. Run `afl-cmin` on the collected corpus, save minimized corpus in `collection_dir.cmin`.
3. Run `afl-tmin` on the remaining samples to reduce them in size. Save results in
   `collection_dir.tmin` if step two was omitted or `collection_dir.cmin.tmin` otherwise.
4. Perform a "dry-run" for each sample and move crashes/timeouts out of the corpus. This
   step will be useful prior to starting a new or resuming a parallel fuzzing job on a
   corpus containing intermittent crashes. Crashes will be moved to a `.crashes` directory,
   if one of steps 1, 2 or 3 were performed. If only "dry-run" is requested crashing
   samples will be moved from the `queue` dirs to the `crashes` within an afl sync dir.  
   
As already indicated, all these steps are optional, making the tool quite flexible. E.g.
running only step four can be handy before resuming a parallel fuzzing session.

Usage:

    afl-minimize [-c COLLECTION_DIR [--cmin] [--tmin]] [-d] [-h] sync_dir -- target_cmd
    
    afl-minimize performs several optimization steps to reduce the size of an afl-
    fuzz corpus.
    
    positional arguments:
      sync_dir              afl synchronisation directory containing multiple
                            fuzzers and their queues.
      target_cmd            Path to the target binary and its command line
                            arguments. Use '@@' to specify crash sample input file
                            position (see afl-fuzz usage).
    
    optional arguments:
      -h, --help            show this help message and exit
      -c COLLECTION_DIR, --collect COLLECTION_DIR
                            Collect all samples from the synchronisation dir and
                            store them in the collection dir. Existing files in
                            the collection directory will be overwritten!
      --cmin                Run afl-cmin on collection dir. Has no effect without
                            '-c'.
      --tmin                Run afl-tmin on minimized collection dir if used
                            together with '--cmin'or on unoptimized collection dir
                            otherwise. Has no effect without '-c'.
      -d, --dry-run         Perform dry-run on collection dir, if '-c' is provided
                            or on synchronisation dir otherwise. Dry-run will move
                            intermittent crashes out of the corpus.


## afl-multicore

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


## afl-multikill

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


## afl-vcrash

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


## Screenshots

### afl-collect

Sample output:

![afl-collect_sample](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_collect_sample.png)

### afl-multicore

Sample output (normal mode):

![afl-multicore_sample](https://raw.githubusercontent.com/rc0r/afl-utils/master/.scrots/afl_multicore_sample.png)

