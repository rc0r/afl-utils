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
from afl_utils import AflThread
from afl_utils.AflPrettyPrint import *

import threading
import queue


def show_info():
    print(clr.CYA + "afl-vcrash " + clr.BRI + "%s" % afl_utils.__version__ + clr.RST + " by %s" % afl_utils.__author__)
    print("Crash verifier for crash samples collected from afl-fuzz.")
    print("")


def verify_samples(num_threads, samples, target_cmd):
    in_queue_lock = threading.Lock()
    out_queue_lock = threading.Lock()
    in_queue = queue.Queue(len(samples))
    out_queue = queue.Queue(len(samples))

    # fill input queue with samples
    in_queue_lock.acquire()
    for s in samples:
        in_queue.put(s)
    in_queue_lock.release()

    thread_list = []

    for i in range(0, num_threads, 1):
        t = AflThread.VerifyThread(i, target_cmd, in_queue, out_queue, in_queue_lock, out_queue_lock)
        thread_list.append(t)
        t.daemon = True
        t.start()

    for t in thread_list:
        t.join()

    crashes_invalid = []
    crashes_timeout = []

    # read invalid samples from output queue
    out_queue_lock.acquire()
    while not out_queue.empty():
        st = out_queue.get()
        if(st[1] == 'invalid'):
            crashes_invalid.append(st[0])
        elif(st[1] == 'timeout'):
            crashes_timeout.append(st[0])
    out_queue_lock.release()

    return crashes_invalid, crashes_timeout


def remove_samples(crash_samples, quiet=True):
    count = 0
    for c in crash_samples:
        if not quiet:
            print(c)

        os.remove(c)
        count += 1

    return count

from afl_utils import afl_collect


def main(argv):
    show_info()

    parser = argparse.ArgumentParser(description="afl-vcrash verifies that afl-fuzz crash samples lead to crashes in \
the target binary.", usage="afl-vcrash [-f LIST_FILENAME] [-h] [-j THREADS] [-q] [-r] collection_dir -- target_command")

    parser.add_argument("collection_dir",
                        help="Directory holding all crash samples that will be verified.")
    parser.add_argument("target_cmd", nargs="+", help="Target binary including command line \
options. Use '@@' to specify crash sample input file position (see afl-fuzz usage).")
    parser.add_argument("-f", "--filelist", dest="list_filename", default=None,
                        help="Writes all crash sample file names that do not lead to crashes into a file.")
    parser.add_argument("-j", "--threads", dest="num_threads", default=1,
                        help="Enable parallel verification by specifying the number of threads afl-vcrash \
will utilize.")
    parser.add_argument("-q", "--quiet", dest="quiet", action="store_const", const=True, default=False,
                        help="Suppress output of crash sample file names that do not lead to crashes. This is \
particularly useful when combined with '-r' or '-f'.")
    parser.add_argument("-r", "--remove", dest="remove", action="store_const", const=True, default=False,
                        help="Remove crash samples that do not lead to crashes.")

    args = parser.parse_args(argv[1:])

    input_dir = os.path.abspath(os.path.expanduser(args.collection_dir))
    if not os.path.exists(input_dir):
        print_err("No valid directory provided for <collection_dir>!")
        return

    num_crashes, crash_samples = afl_collect.get_samples_from_dir(input_dir, True)

    print_ok("Verifying %d crash samples..." % num_crashes)

    args.target_cmd = " ".join(args.target_cmd).split()
    args.target_cmd[0] = os.path.abspath(os.path.expanduser(args.target_cmd[0]))
    if not os.path.exists(args.target_cmd[0]):
        print_err("Target binary not found!")
        return
    args.target_cmd = " ".join(args.target_cmd)

    invalid_samples, timeout_samples = verify_samples(int(args.num_threads), crash_samples, args.target_cmd)

    print_warn("Found %d invalid crash samples." % len(invalid_samples))
    print_warn("%d samples caused a timeout." % len(timeout_samples))

    if args.remove:
        print_ok("Removing invalid crash samples.")
        remove_samples(invalid_samples, args.quiet)
        print_ok("Removing timeouts.")
        remove_samples(timeout_samples, args.quiet)
    elif not args.quiet:
        for ci in invalid_samples:
            print(ci)

    # generate filelist of collected crash samples
    if args.list_filename:
        afl_collect.generate_sample_list(args.list_filename, invalid_samples + timeout_samples)
        print_ok("Generated invalid crash sample list '%s'." % args.list_filename)


if __name__ == "__main__":
    from afl_utils import afl_collect
    main(sys.argv)
