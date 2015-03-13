#!/usr/bin/env python

import argparse
import os
import shutil
import subprocess
import sys

import afl_utils
from afl_utils import afl_vcrash
from db_connectors import con_sqlite


# afl-collect global settings
global_crash_subdir = "crashes/"
global_exclude_files = [
    "README.txt",
]

# gdb settings

# Path to gdb binary
gdb_binary = "/usr/bin/gdb"

# Path to 'exploitable.py' (https://github.com/jfoote/exploitable)
# Set to None if you already source exploitable.py in your .gdbinit file!
gdb_exploitable_path = None

# Path to 'afl_util_exit_handler.py'
# Set to None if you already source afl_util_exit_handler.py in your .gdbinit file!
gdb_exit_handler_path = "gdb/afl_util_exit_handler.py"


def show_info():
    print("afl-collect %s by %s" % (afl_utils.__version__, afl_utils.__author__))
    print("Crash sample collection and processing utility for afl-fuzz.")
    print("")


def get_fuzzer_instances(sync_dir):
    fuzzer_inst = []
    for fdir in os.listdir(sync_dir):
        if os.path.isdir(os.path.join(sync_dir, fdir)):
            fuzzer_inst.append(fdir)
    return fuzzer_inst


def get_crash_samples(fuzzer_subdir, abs_path=False):
    crashes = []
    num_crashes = 0
    for f in os.listdir(fuzzer_subdir):
        if os.path.isfile(os.path.join(fuzzer_subdir, f)) and f not in global_exclude_files:
            if abs_path:
                crashes.append(os.path.join(fuzzer_subdir, f))
            else:
                crashes.append(f)
            num_crashes += 1
    return num_crashes, crashes


def copy_crash_samples(fuzzer_subdir, fuzzer, out_dir, files_collected):
    crash_sample_num, samples = get_crash_samples(fuzzer_subdir)
    for c in samples:
        shutil.copyfile(os.path.join(fuzzer_subdir, c), os.path.join(out_dir, "%s:%s" % (fuzzer, c)))
        files_collected.append(os.path.join(out_dir, "%s:%s" % (fuzzer, c)))

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

    # source afl_utils_exit_handler.py if necessary
    if gdb_exit_handler_path:
        fd.writelines("source %s\n" % os.path.join(os.getcwd(), gdb_exit_handler_path))

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
                                     usage="afl_collect.py [-d DATABASE] [-e GDB_EXPL_SCRIPT_FILE] [-f LIST_FILENAME]\n \
[-g GDB_SCRIPT_FILE] [-h] [-r] sync_dir collection_dir target_cmd")

    parser.add_argument("sync_dir", help="afl synchronisation directory crash samples  will be collected from.")
    parser.add_argument("collection_dir",
                        help="Output directory that will hold a copy of all crash samples and other generated files. \
Existing files in the collection directory will be overwritten!")
    parser.add_argument("-d", "--database", dest="database_file", help="Submit classification data into a sqlite3 \
database.", default=None)
    parser.add_argument("-e", "--execute-gdb-script", dest="gdb_expl_script_file",
                        help="Execute a gdb+exploitable script after crash sample collection for crash classification.",
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

    overall_crash_sample_num = 0
    files_collected = []
    for f in fuzzers:
        (crash_sample_num, files_collected) = copy_crash_samples(os.path.join(sync_dir, f, global_crash_subdir), f,
                                                                 out_dir, files_collected)
        overall_crash_sample_num += crash_sample_num

    print("Successfully copied %d crash samples to %s" % (overall_crash_sample_num, out_dir))

    if args.remove_invalid:
        invalid_num, invalid_samples = afl_vcrash.verify_samples(files_collected, args.target_cmd)
        print("Found %d invalid crash samples. Cleaning up..." % invalid_num)
        for ci in invalid_samples:
            files_collected.remove(ci)
            os.remove(ci)
            overall_crash_sample_num -= 1

    # generate filelist of collected crash samples
    if args.list_filename:
        print("Generating crash sample list file %s" % args.list_filename)
        generate_crash_sample_list(os.path.join(out_dir, args.list_filename), files_collected)

    # generate gdb+exploitable script
    if args.gdb_script_file:
        generate_gdb_exploitable_script(os.path.join(out_dir, args.gdb_script_file), files_collected, args.target_cmd)

    # execute gdb+exploitable script
    if args.gdb_expl_script_file:
        classification_data = execute_gdb_script(out_dir, args.gdb_expl_script_file, overall_crash_sample_num)

        """
        TODO: Make use of classification data (database submission, crash sample reduction, ...)
        """

        if args.database_file:
            lite_db = con_sqlite.sqliteConnector(args.database_file)

            lite_db.init_database()

            for dataset in classification_data:
                if not lite_db.dataset_exists(dataset):
                    lite_db.insert_dataset(dataset)


if __name__ == "__main__":
    main(sys.argv)