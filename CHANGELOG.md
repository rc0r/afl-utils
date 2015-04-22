### afl-utils Changelog

Release | Description
:-------:|----
1.02a | Optimizations for afl_collect to reduce/eliminate file cp/rm operations
1.01a | De-duplication via exploitable backtrace hashes added to afl_collect 
1.00a | stdin support added to afl_vcrash and afl_collect
0.23a | afl_multikill added
0.22a | Screen mode added to afl_multicore
0.21a | Initial version of afl_multicore added
0.20a | Sample collection from all `crashes*` sub directories added, minor bug fix for sample cleanup
0.19a | Added auto-cleanup feature for samples leading to uninteresting crashes
0.18a | Fixed gdb+exploitable script interruptions that occur on graceful exits of the target binary
0.17a | Basic SQLite3 database support added
0.16a | Minor bug fix for gdb+exploitable script generation
0.15a | Code refactoring, minor bug fixes
0.14a | gdb+exploitable script execution and output parsing added for easy crash classification
0.13a | Auto-cleanup of invalid crash samples added
0.12a | gdb+exploitable script generation added
0.11a | Crash sample file list creation added, afl_vcrash added
0.10a | Initial release, just collect crash sample files
