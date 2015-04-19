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
import subprocess
import sys

import afl_utils
import afl_utils.afl_collect


def show_info():
    print("afl_vcrash %s by %s" % (afl_utils.__version__, afl_utils.__author__))
    print("Crash verifier for crash samples collected from afl-fuzz.")
    print("")


def verify_samples(crash_samples, target_cmd):
    crashes_invalid = []
    num_invalid = 0
    cmd_string = " ".join(target_cmd)
    for cs in crash_samples:
        if afl_utils.afl_collect.stdin_mode(cmd_string):
            cmd_string += " < @@"
        cmd = cmd_string.replace("@@", cs)
        try:
            v = subprocess.call(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True, timeout=60)
            # check if process was terminated/stopped by signal
            if not os.WIFSIGNALED(v) and not os.WIFSTOPPED(v):
                num_invalid += 1
                crashes_invalid.append(cs)
            else:
                # need extension (add uninteresting signals):
                # following signals don't indicate hard crashes: 1
                # os.WTERMSIG(v) ?= v & 0x7f ???
                if (os.WTERMSIG(v) or os.WSTOPSIG(v)) in [1]:
                    num_invalid += 1
                    crashes_invalid.append(cs)
                # debug
                #else:
                #    if os.WIFSIGNALED(v):
                #        print("%s: sig: %d (%d)" % (cs, os.WTERMSIG(v), v))
                #    elif os.WIFSTOPPED(v):
                #        print("%s: sig: %d (%d)" % (cs, os.WSTOPSIG(v), v))
        except Exception:
            pass

    return num_invalid, crashes_invalid


def remove_samples(crash_samples, quiet=True):
    count = 0
    for c in crash_samples:
        if not quiet:
            print(c)
        os.remove(c)
        count += 1

    return count


def main(argv):
    show_info()

    parser = argparse.ArgumentParser(description="afl-vcrash verifies that afl-fuzz crash samples lead to crashes in \
the target binary.", usage="afl_vcrash [-h] [-f LIST_FILENAME] [-q] [-r] collection_dir target_command \
[target_command_args]")

    parser.add_argument("collection_dir",
                        help="Directory holding all crash samples that will be verified.")
    parser.add_argument("target_command", nargs="+", help="Target binary including command line \
options. Use '@@' to specify crash sample input file position (see afl-fuzz usage).")
    parser.add_argument("-f", "--filelist", dest="list_filename", default=None,
                        help="Writes all crash sample file names that do not lead to crashes into a file.")
    parser.add_argument("-q", "--quiet", dest="quiet", action="store_const", const=True, default=False,
                        help="Suppress output of crash sample file names that do not lead to crashes. This is \
particularly useful when combined with '-r' or '-f'.")
    parser.add_argument("-r", "--remove", dest="remove", action="store_const", const=True, default=False,
                        help="Remove crash samples that do not lead to crashes.")

    args = parser.parse_args(argv[1:])

    if args.collection_dir:
        input_dir = args.collection_dir
    else:
        print("No valid directory provided for <collection_dir>!")
        return

    num_crashes, crash_samples = afl_collect.get_crash_samples_from_dir(input_dir, True)

    print("Verifying %d crash samples..." % num_crashes)

    num_invalid, invalid_samples = verify_samples(crash_samples, args.target_command)

    print("Found %d invalid crash samples" % num_invalid)

    if args.remove:
        remove_samples(invalid_samples, args.quiet)
    elif not args.quiet:
        for ci in invalid_samples:
            print(ci)

    # generate filelist of collected crash samples
    if args.list_filename:
        print("Generating invalid crash sample list file %s" % args.list_filename)
        afl_collect.generate_crash_sample_list(args.list_filename, invalid_samples)


if __name__ == "__main__":
    from afl_utils import afl_collect
    main(sys.argv)
