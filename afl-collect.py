#!/usr/bin/env python


import argparse
import os
import shutil
import sys

# afl-collect info
version = "0.11b"
author = "rc0r (@_rc0r)"

# afl-collect global settings
global_crash_subdir = "crashes/"
global_exlude_files = [
    "README.txt",
]


def show_info():
    print("afl-collect %s by %s" % (version, author))
    print("crash sample collection utility for afl-fuzz.")
    print("")


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


def generate_crash_sample_list(list_filename, files_collected):
    print("Generating crash sample list file %s" % list_filename)
    fd = open(list_filename, "w")

    if not fd:
        print("Error: Could not create filelist %s!" % list_filename)
        return

    for f in files_collected:
        fd.writelines("%s\n" % f)

    fd.close()


def main(argv):
    show_info()

    parser = argparse.ArgumentParser(description="afl-collect copies all crash sample files from an afl sync dir used \
by multiple fuzzers when fuzzing in parallel into a single location providing easy access for further crash analysis.")

    parser.add_argument("sync_dir", help="afl synchronisation directory crash samples  will be collected from.")
    parser.add_argument("collection_dir",
                        help="Output directory that will hold a copy of all crash samples and other generated files. \
Existing files in the collection directory will be overwritten!")
    parser.add_argument("-f", "--filelist", dest="list_filename", default=None,
                        help="Writes all collected crash sample filenames into a file in the collection directory.")

    args = parser.parse_args(argv[1:])

    if args.sync_dir:
        sync_dir = args.sync_dir
    else:
        print("No valid directory provided for <SYNC_DIR>!")
        return

    if args.collection_dir:
        out_dir = args.collection_dir
    else:
        print("No valid directory provided for <OUT_DIR>!")
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

    # generate filelist of collected crash samples
    if args.list_filename:
        generate_crash_sample_list(os.path.join(out_dir, args.list_filename), files_collected)


main(sys.argv)
