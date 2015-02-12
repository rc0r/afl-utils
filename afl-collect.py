#!/usr/bin/env python


import os
import shutil
import sys

version = "0.10b"
author = "rc0r (@_rc0r)"

global_crash_subdir = "crashes/"
global_exlude_files = [
    "README.txt",
]


def show_info():
    print("afl-collect %s by %s" % (version, author))
    print("crash sample collection utility for afl-fuzz.")
    print("")


def show_help():
    print("afl-collect copies all crash sample files from an afl sync")
    print("dir used by multiple fuzzers when fuzzing in parallel into")
    print("a single location providing easy access for further crash")
    print("analysis.")
    print("")
    print("Usage: afl-collect.py <afl-sync-dir> <collection-dir>")


def get_fuzzer_instances(sync_dir):
    fuzzer_inst = []
    for dir in os.listdir(sync_dir):
        if os.path.isdir(os.path.join(sync_dir, dir)):
            fuzzer_inst.append(dir)
    return fuzzer_inst


def get_crash_samples(fuzzer_subdir):
    crashes = []
    for f in os.listdir(fuzzer_subdir):
        if os.path.isfile(os.path.join(fuzzer_subdir, f)) and f not in global_exlude_files:
            crashes.append(f)
    return crashes


def copy_crash_samples(fuzzer_subdir, fuzzer, out_dir, files_collected):
    crash_sample_num = 0
    for c in get_crash_samples(fuzzer_subdir):
        shutil.copyfile(os.path.join(fuzzer_subdir, c), os.path.join(out_dir, "%s:%s" % (fuzzer, c)))
        files_collected.append(os.path.join(out_dir, "%s:%s" % (fuzzer, c)))
        crash_sample_num += 1

    return crash_sample_num, files_collected


def main(argv):
    show_info()
    if len(argv) != 3:
        show_help()
        return

    if os.path.isdir(argv[1]):
        sync_dir = argv[1]
    else:
        print("No valid directory provided for <afl-sync-dir>!")
        return

    if os.path.isdir(argv[2]):
        out_dir = argv[2]
    else:
        print("No valid directory provided for <collection-dir>!")
        return

    print("Going to collect crash samples from: %s" % sync_dir)

    fuzzers = get_fuzzer_instances(sync_dir)
    print("Found %d fuzzers, collecting crash samples." % len(fuzzers))

    overall_crash_sample_num = 0
    files_collected = []
    for f in fuzzers:
        (crash_sample_num, files_collected) = copy_crash_samples(os.path.join(sync_dir, f, global_crash_subdir), f,
                                                                 out_dir, files_collected)
        overall_crash_sample_num += crash_sample_num

    print("Successfully copied %d crash samples to %s" % (overall_crash_sample_num, out_dir))
    #print(files_collected)

main(sys.argv)