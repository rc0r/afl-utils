# Contributing

If you're missing some feature in afl-utils or like to propose some changes, I'd appreciate
your contributions. Just send your bug reports, feature ideas, code patches or pull requests
either via Github or directly to `hlt99 at blinkenshell dot org`!  
The main development branch is `experimental` whereas `master` only contains stable code and
releases. Be sure to check both branches and decide which one is more appropriate for your
changes! Usually this is `experimental` since it might contain changes that are still in
testing phase but are meant to be merged into `master` later on.  
**Attention:** Make sure that your changes do **not** break any tests before sending your
patches and pull requests! Run `python setup.py test` to invoke the test suite after you
modified parts of the code! If your patch introduces a new feature, please be so kind to
provide appropriate test cases for it!

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

