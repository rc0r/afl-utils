# Installation

The first thing to do is to install all required software packages if necessary. I'll
assume you've got Python 3 running and have got installed the other required tools.
Python package requirements should be automatically handled by the setup script
`setup.py` (see below).

## Dependencies

* Python3.4
* Python `sqlite3` package for database support
* `nohup` for `afl-multicore` normal mode (I'm using: 8.23 (GNU coreutils))
* `screen` for `afl-multicore` interactive/screen mode (I'm using: GNU Screen 4.02.01)
* `gdb` with Python support (for gdb script execution support)
* [Patched Exploitable](https://github.com/rc0r/exploitable) (for gdb script execution support)
* and of course you'll need [afl](http://lcamtuf.coredump.cx/afl/) for `afl-multicore`, `afl-multikill`


## Set up exploitable

In order to use advanced afl-utils features exploitable needs to be installed and
set up to work with `gdb`.

Get the patched version from GH:  

    $ git clone https://github.com/rc0r/exploitable

Next install exploitable globally or locally according to the instructions in the
`Usage` section of exploitables' `README.md`!

## afl-utils Installation

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
