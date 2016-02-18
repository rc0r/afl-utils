"""
Copyright 2015-2016 @_rc0r <hlt99@blinkenshell.org>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import argparse
import os
import sys
import signal

import afl_utils
from afl_utils.AflPrettyPrint import clr, print_err, print_ok, print_warn


def show_info():
    print(clr.CYA + "afl-multikill " + clr.BRI + "%s" % afl_utils.__version__ + clr.RST +
          " by %s" % afl_utils.__author__)
    print("Wrapper script to easily abort non-interactive afl-multicore sessions.")
    print("")


def kill_session(session):
    if os.path.isfile("/tmp/afl_multicore.PGID.%s" % session):
        f = open("/tmp/afl_multicore.PGID.%s" % session)
        pgids = f.readlines()

        for pgid in pgids:
            try:
                print_ok("Killing jobs with PGID %s" % pgid.strip('\r\n'))
                os.killpg(int(pgid), signal.SIGTERM)
            except ProcessLookupError:
                print_warn("No processes with PGID %s found!" % (pgid.strip('\r\n')))

        f.close()
        os.remove("/tmp/afl_multicore.PGID.%s" % session)
    else:
        print_err("PGID file '/tmp/afl_multicore.PGID.%s' not found! Aborting!" % session)
        sys.exit(1)


def main(argv):
    show_info()

    parser = argparse.ArgumentParser(description="afl-multikill aborts all afl-fuzz instances belonging to an active \
afl-multicore session. Interactive screen sessions are not supported!",
                                     usage="afl-multikill [-S SESSION]")

    parser.add_argument("-S", "--session", dest="session",
                        help="afl-multicore session to abort (Default='SESSION').", default="SESSION")

    args = parser.parse_args(argv[1:])

    kill_session(args.session)
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
