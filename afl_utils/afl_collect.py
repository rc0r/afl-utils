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
import shutil
import subprocess
import sys

import afl_utils
from afl_utils import afl_vcrash
from db_connectors import con_sqlite


# afl-collect global settings
global_crash_subdirs = "crashes"
global_exclude_files = [
    "README.txt",
]

# gdb settings

# Path to gdb binary
gdb_binary = "/usr/bin/gdb"

# Path to 'exploitable.py' (https://github.com/rc0r/exploitable)
# Set to None if you already source exploitable.py in your .gdbinit file!
gdb_exploitable_path = None


def show_info():
    print("afl_collect %s by %s" % (afl_utils.__version__, afl_utils.__author__))
    print("Crash sample collection and processing utility for afl-fuzz.")
    print("")


def get_fuzzer_instances(sync_dir):
    fuzzer_inst = []
    for fdir in os.listdir(sync_dir):
        if os.path.isdir(os.path.join(sync_dir, fdir)):
            fuzzer_inst.append((fdir, []))

    fuzzer_inst = get_crash_directories(sync_dir, fuzzer_inst)

    return fuzzer_inst


def get_crash_directories(sync_dir, fuzzer_instances):
    for fi in fuzzer_instances:
        fuzz_dir = os.path.join(sync_dir, fi[0])
        for cdir in os.listdir(fuzz_dir):
            if os.path.isdir(os.path.join(fuzz_dir, cdir)) and global_crash_subdirs in cdir:
                fi[1].append(cdir)

    return fuzzer_instances


def get_crash_samples_from_dir(crash_subdir, abs_path=False):
    crashes = []
    num_crashes = 0
    for f in os.listdir(crash_subdir):
        if os.path.isfile(os.path.join(crash_subdir, f)) and f not in global_exclude_files:
            if abs_path:
                crashes.append(os.path.join(crash_subdir, f))
            else:
                crashes.append(f)
            num_crashes += 1
    return num_crashes, crashes


def collect_crash_samples(sync_dir, fuzzer_instances):
    crashes = []
    num_crashes = 0
    for fi in fuzzer_instances:
        fuzz_dir = os.path.join(sync_dir, fi[0])
        fuzz_crashes = []

        for cd in fi[1]:
            tmp_num_crashes, tmp_crashes = get_crash_samples_from_dir(os.path.join(fuzz_dir, cd))
            fuzz_crashes.append((cd, tmp_crashes))
            num_crashes += tmp_num_crashes

        crashes.append((fi[0], fuzz_crashes))

    return num_crashes, crashes


def copy_crash_samples(sync_dir, fuzzer_instances, out_dir):
    crash_sample_num, samples = collect_crash_samples(sync_dir, fuzzer_instances)
    files_collected = []

    for f in samples:
        for cd in f[1]:
            for c in cd[1]:
                shutil.copyfile(os.path.join(sync_dir, f[0], cd[0], c), os.path.join(out_dir, "%s:%s" % (f[0], c)))
                files_collected.append(os.path.join(out_dir, "%s:%s" % (f[0], c)))

    return crash_sample_num, files_collected


def generate_crash_sample_list(list_filename, files_collected):
    fd = open(list_filename, "w")

    if not fd:
        print("Error: Could not create filelist %s!" % list_filename)
        return

    for f in files_collected:
        fd.writelines("%s\n" % f)

    fd.close()


def generate_gdb_exploitable_script(script_filename, files_collected, target_cmd):
    target_cmd = " ".join(target_cmd)
    target_cmd = target_cmd.split()
    gdb_target_binary = target_cmd[0]
    gdb_run_cmd = " ".join(target_cmd[1:])
    print("Generating gdb+exploitable script %s for %d samples" % (script_filename, len(files_collected)))
    fd = open(script_filename, "w")
    if not fd:
        print("Could not open script file %s for writing!" % script_filename)
        return

    #<script header>
    # source exploitable.py if necessary
    if gdb_exploitable_path:
        fd.writelines("source %s\n" % gdb_exploitable_path)

    # load executable
    fd.writelines("file %s\n" % gdb_target_binary)
    #</script_header>

    # fill script with content
    for f in files_collected:
        run_cmd = "run " + gdb_run_cmd + "\n"
        run_cmd = run_cmd.replace("@@", f)
        fd.writelines("echo Crash\ sample:\ '%s'\\n\n" % f)
        fd.writelines(run_cmd)
        fd.writelines("exploitable\n")

    #<script_footer>
    fd.writelines("quit")
    #</script_footer>

    fd.close()


# ok, this needs improvement!!!
def execute_gdb_script(out_dir, script_filename, num_samples):
    classification_data = []
    print("Executing gdb+exploitable script %s" % script_filename)

    out_dir = os.path.expanduser(out_dir) + "/"

    script_args = [
        str(gdb_binary),
        "-x",
        str(os.path.join(out_dir, script_filename)),
    ]

    grep_for = [
        "Crash sample: '",
        "Exploitability Classification: ",
        "Short description: ",
    ]

    try:
        script_output = subprocess.check_output(" ".join(script_args), shell=True, stderr=subprocess.DEVNULL,
                                                universal_newlines=True)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        script_output = e.output

    script_output = script_output.splitlines()

    grepped_output = []

    for line in script_output:
        matching = [line.replace(g, '') for g in grep_for if g in line]
        matching = " ".join(matching).strip('\' ')
        matching = matching.replace(out_dir, '')
        if len(matching) > 0:
            grepped_output.append(matching)

    i = 1
    print("*** GDB+EXPLOITABLE SCRIPT OUTPUT ***")
    for g in range(0, len(grepped_output)-2, 3):
        print("[%05d] %s: %s [%s]" % (i, grepped_output[g].ljust(64, '.'), grepped_output[g+2], grepped_output[g+1]))
        classification_data.append([grepped_output[g], grepped_output[g+2], grepped_output[g+1]])
        i += 1

    if i < num_samples:
        #print("[%05d] %s: INVALID SAMPLE (please remove and run 'gdb -x %s' manually)" % (i, grepped_output[-1].ljust(64, '.'), script_filename))
        print("[%05d] %s: INVALID SAMPLE (Aborting!)" % (i, grepped_output[-1].ljust(64, '.')))
        print("Returned data may be incomplete!")
    print("*** ***************************** ***")

    return classification_data


def main(argv):
    show_info()

    parser = argparse.ArgumentParser(description="afl_collect copies all crash sample files from an afl sync dir used \
by multiple fuzzers when fuzzing in parallel into a single location providing easy access for further crash analysis.",
                                     usage="afl_collect [-d DATABASE] [-e|-g GDB_EXPL_SCRIPT_FILE] [-f LIST_FILENAME]\n \
[-h] [-r] [-rr] sync_dir collection_dir target_cmd")

    parser.add_argument("sync_dir", help="afl synchronisation directory crash samples  will be collected from.")
    parser.add_argument("collection_dir",
                        help="Output directory that will hold a copy of all crash samples and other generated files. \
Existing files in the collection directory will be overwritten!")
    parser.add_argument("-d", "--database", dest="database_file", help="Submit classification data into a sqlite3 \
database. Has no effect without '-e'.", default=None)
    parser.add_argument("-e", "--execute-gdb-script", dest="gdb_expl_script_file",
                        help="Generate and execute a gdb+exploitable script after crash sample collection for crash \
classification. (Like option '-g', plus script execution.)",
                        default=None)
    parser.add_argument("-f", "--filelist", dest="list_filename", default=None,
                        help="Writes all collected crash sample filenames into a file in the collection directory.")
    parser.add_argument("-g", "--generate-gdb-script", dest="gdb_script_file",
                        help="Generate gdb script to run 'exploitable.py' on all collected crash samples. Generated \
script will be placed into collection directory.", default=None)
    parser.add_argument("-r", "--remove-invalid", dest="remove_invalid", action="store_const", const=True,
                        default=False, help="Verify collected crash samples and remove samples that do not lead to \
crashes (runs 'afl_vcrash.py -r' on collection directory). This step is done prior to any script file \
or file list generation/execution.")
    parser.add_argument("-rr", "--remove-unexploitable", dest="remove_unexploitable", action="store_const", const=True,
                        default=False, help="Remove crash samples that have an exploitable classification of \
'NOT_EXPLOITABLE', 'PROBABLY_NOT_EXPLOITABLE' or 'UNKNOWN'. Sample file removal will take place after gdb+exploitable \
script execution. Has no effect without '-e'.")
    parser.add_argument("target_cmd", nargs="+", help="Path to the target binary and its command line arguments. \
Use '@@' to specify crash sample input file position (see afl-fuzz usage).")

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

    (overall_crash_sample_num, files_collected) = copy_crash_samples(sync_dir, fuzzers, out_dir)

    print("Successfully copied %d crash samples to %s" % (overall_crash_sample_num, out_dir))

    if args.remove_invalid:
        invalid_num, invalid_samples = afl_vcrash.verify_samples(files_collected, args.target_cmd)
        print("Found %d invalid crash samples. Cleaning up..." % invalid_num)
        for ci in invalid_samples:
            # remove all occurrences of invalid sample
            files_collected = [s for s in files_collected if s != ci]

        overall_crash_sample_num -= afl_vcrash.remove_samples(invalid_samples)

    # generate filelist of collected crash samples
    if args.list_filename:
        print("Generating crash sample list file %s" % args.list_filename)
        generate_crash_sample_list(os.path.join(out_dir, args.list_filename), files_collected)

    # generate gdb+exploitable script
    if args.gdb_expl_script_file:
        generate_gdb_exploitable_script(os.path.join(out_dir, args.gdb_expl_script_file), files_collected,
                                        args.target_cmd)

        # execute gdb+exploitable script
        classification_data = execute_gdb_script(out_dir, args.gdb_expl_script_file, overall_crash_sample_num)

        # Submit crash classification data into database
        if args.database_file:
            lite_db = con_sqlite.sqliteConnector(args.database_file)

            lite_db.init_database()

            for dataset in classification_data:
                if not lite_db.dataset_exists(dataset):
                    lite_db.insert_dataset(dataset)

        # remove crash samples that are classified uninteresting/unknown
        if args.remove_unexploitable:
            classification_unexploitable = [
                'NOT_EXPLOITABLE',
                'PROBABLY_NOT_EXPLOITABLE',
                'UNKNOWN'
            ]

            uninteresting_samples = []

            for c in classification_data:
                if c[1] in classification_unexploitable:
                    uninteresting_samples.append(os.path.join(out_dir, c[0]))

            remove_count = afl_vcrash.remove_samples(uninteresting_samples)
            overall_crash_sample_num -= remove_count
            print("%d uninteresting crash samples removed. Leaving %d samples in the output directory." %
                  (remove_count, overall_crash_sample_num))
    elif args.gdb_script_file:
        generate_gdb_exploitable_script(os.path.join(out_dir, args.gdb_script_file), files_collected, args.target_cmd)


if __name__ == "__main__":
    main(sys.argv)