# afl-utils Changelog

Version 1.16a

  - afl-stat shows diffs of current and last stat.
  - afl-stat auto-shortens statuses to 140 chars.
  - afl-stat interval configuration setting is now a float. Thus polling
    intervals of less than one minute can be configured.

Version 1.15a

  - User comment field added in Data table of afl-collect crash database. Update
    your existing databases accordingly!
  - Added afl-stats for status printing and tweeting.

Version 1.14a

  - Path handling in afl-multicore improved.
  - Uninitialized variable bugs fixed in afl-collect.
  - afl-minimize now supports parallel afl-tmin invocation.

Version 1.13a

  - Added multi-threaded dry-runs in afl-minimize.

Version 1.12a

  - Target command path handling in afl-vcrash fixed.
  - Handling non-UTF-8 characters in afl-collect fixed (by Mark Janssen).
  - Incremental mode added to afl-collect: When afl-collect is pointed to an existing database,
    afl-collect will now skip samples having an entry in the database. This should be useful 
    subsequent afl-collect runs on huge crash dirs.

## Old Releases

Release | Description
:-------:|---- 
1.11a | Minor bug-fix in afl-multicore, some explanations for afl-minimize added to README.md
1.10a | afl-minimize added, bug fixed in AflThread.py
1.09a | Docs refactored, target command path handling improved, bug-fix in afl-collect when collecting crashes without further processing
1.08a | `setup.py` added, tools names refactored to comply with afl naming scheme
1.07a | Minor afl-collect and afl-multikill bugs fixed. afl-collect will keep/collect crashes classified as 'UNKNOWN'
1.06a | Added flag `--afl-args` to afl-multicore to set custom afl command line options
1.05a | Added flag `--env-vars` to afl-multicore to set environment variables in all windows when using interactive screen mode
1.04a | Multi-threaded gdb script execution added
1.03a | Parallel sample verification support added to afl-vcrash
1.02a | Optimizations for afl-collect to reduce/eliminate file cp/rm operations
1.01a | De-duplication via exploitable backtrace hashes added to afl-collect 
1.00a | stdin support added to afl-vcrash and afl-collect
0.23a | afl-multikill added
0.22a | Screen mode added to afl-multicore
0.21a | Initial version of afl-multicore added
0.20a | Sample collection from all `crashes*` sub directories added, minor bug fix for sample cleanup
0.19a | Added auto-cleanup feature for samples leading to uninteresting crashes
0.18a | Fixed gdb+exploitable script interruptions that occur on graceful exits of the target binary
0.17a | Basic SQLite3 database support added
0.16a | Minor bug fix for gdb+exploitable script generation
0.15a | Code refactoring, minor bug fixes
0.14a | gdb+exploitable script execution and output parsing added for easy crash classification
0.13a | Auto-cleanup of invalid crash samples added
0.12a | gdb+exploitable script generation added
0.11a | Crash sample file list creation added, afl-vcrash added
0.10a | Initial release, just collect crash sample files
