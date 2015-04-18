"""
Copyright 2015 @_rc0r <hlt99@blinkenshell.org>

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

import afl_utils


def show_info():
    print("afl_multikill %s by %s" % (afl_utils.__version__, afl_utils.__author__))
    print("Wrapper script to easily abort non-interactive afl_multicore sessions.")
    print("")


def kill_session(session):
    if os.path.isfile("/tmp/afl_multicore.PID.%s" % session):
        f = open("/tmp/afl_multicore.PID.%s" % session)
        pid_list = f.readlines()

        for pid in pid_list:
            print("Killing job with PID %s" % pid.strip('\r\n'))
            os.kill(int(pid), 9)

        f.close()
        os.remove("/tmp/afl_multicore.PID.%s" % session)
    else:
        print("Fatal error: PID file '/tmp/afl_multicore.PID.%s' not found! Aborting!" % session)


def main(argv):
    show_info()

    parser = argparse.ArgumentParser(description="afl_multikill aborts all afl-fuzz instances belonging to an active \
afl_multicore session. Interactive screen sessions are not supported!",
                                     usage="afl_multikill [-S SESSION]")

    parser.add_argument("-S", "--session", dest="session",
                        help="afl_multicore session to abort (Default='SESSION').", default="SESSION")

    args = parser.parse_args(argv[1:])

    kill_session(args.session)


if __name__ == "__main__":
    main(sys.argv)