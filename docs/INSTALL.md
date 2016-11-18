# Installation

The first thing to do is to install all required software packages if necessary. I'll
assume you've got Python 3 running and have got installed the other required tools.
Python package requirements should be automatically handled by the setup script
`setup.py` (see below).


## Dependencies

* Python3.4
* Python `sqlite3` package for database support (auto-installed)
* Python `twitter` package for `afl-stat` support (auto-installed)
* `nohup` for `afl-multicore` normal mode (I'm using: 8.23 (GNU coreutils))
* `screen` for `afl-multicore` interactive/screen mode (I'm using: GNU Screen 4.02.01)
* `gdb` with Python support (for gdb script execution support)
* [Patched Exploitable](https://github.com/rc0r/exploitable) (for gdb script execution support) (auto-installed)
* and of course you'll need [afl](http://lcamtuf.coredump.cx/afl/) for `afl-multicore`, `afl-multikill`


## Set up exploitable

In order to use advanced afl-utils features exploitable needs to be installed and
set up to work with `gdb`.

Since `v1.19a` the patched version is auto-installed when installing `afl-utils` using
`setup.py`. See next section for instructions!

However, if you want to install exploitable manually, get the patched version from GH:  

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

    $ virtualenv -p python3 venv
    $ source venv/bin/activate
    $ python setup.py install

If at any time something goes wrong, just remove the `venv` directory and start
all over with a fresh environment!

This will also fetch and install Python `twitter` and `exploitable` packages into
your Python environment.
**Attention:** Make sure you source `exploitable.py` in your `~/.gdbinit` file as
inidicated by the `exploitable` installer! Otherwise `gdb` won't recognize
`exploitable` and the advanced features of `afl-collect` are not going to work
properly!

If you like, you can run tests with:

    $ python setup.py test

However, running tests is optional, but might be a good idea when installing
experimental builds. Now you're good to start:

    $ afl-collect --help


## afl-stats setup

For `afl-stats` to work, you'll have to create a Twitter application at
[Twitter Dev](https://dev.twitter.com/apps). Put your `consumer_key` and `consumer_secret`
tokens in an `afl-stats` configuration file:

    $ cp afl-stats.conf.sample afl-stats.conf
    # now edit afl-stats.conf to your needs
    
The sample configuration file `afl-stats.conf.sample` is quite self-explanatory. Once
you've finished configuration. Start `afl-stats`:

    $ afl-stats
    
On the first run `afl-stats` needs to be authorized with your Twitter account. This is done
using OAuth. A browser window should pop up, asking for permission to access your Twitter
account. Once confirmed a PIN code is displayed that must be entered into `afl-stats` as
asked. Most of the time this process is quite straight-forward.

