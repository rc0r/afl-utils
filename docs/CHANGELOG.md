### afl-utils Changelog

Release | Description
:-------:|----
1.10a | afl-minimize added
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
