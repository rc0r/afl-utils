# Feature Ideas / ToDo

- [ ] implement configurable timeout for afl-collect, afl-minimize (like `-t` flag in `afl-vcrash`)
- [x] increase test coverage
- [x] submit classification data into some sort of database
    - [x] basic sqlite3 database support added
    - [ ] want more db connectors? Drop me a line!
- [x] afl-multicore: wrapper script that starts multiple afl-instances for parallel fuzzing on multiple cores
    - [x] screen mode
    - [ ] tmux mode (only, if requested explicitly)
    - [x] afl-stats for checking fuzzer_stats
