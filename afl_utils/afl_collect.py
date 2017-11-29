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
import exploitable
import os
import queue
import shutil
import sys
import threading

import afl_utils
from afl_utils import SampleIndex, AflThread
from afl_utils.AflPrettyPrint import clr, print_ok, print_err, print_warn
from db_connectors import con_sqlite

# afl-collect global settings
global_crash_subdirs = "crashes"
global_queue_subdirs = "queue"
global_exclude_files = [
    "README.txt",
]

fuzzer_stats_filename = "fuzzer_stats"

# gdb settings

# Path to gdb binary
gdb_binary = shutil.which("gdb")


# afl-collect database table spec
db_table_spec = """`Sample` TEXT PRIMARY KEY NOT NULL, `Classification` TEXT NOT NULL,
`Classification_Description` TEXT NOT NULL, `Hash` TEXT, `User_Comment` TEXT"""


def check_gdb():
    if gdb_binary is None:
        print_err("gdb binary not found!")
        sys.exit(1)


def show_info():
    print(clr.CYA + "afl-collect " + clr.BRI + "%s" % afl_utils.__version__ + clr.RST + " by %s" % afl_utils.__author__)
    print("Crash sample collection and processing utility for afl-fuzz.")
    print("")


def get_fuzzer_instances(sync_dir, crash_dirs=True):
    if not os.path.isabs(sync_dir):
        sync_dir = os.path.abspath(sync_dir)

    fuzzer_inst = []
    fuzzer_stats_file = os.path.join(sync_dir, fuzzer_stats_filename)
    if os.path.exists(fuzzer_stats_file) and os.path.isfile(fuzzer_stats_file):
        # we're inside a single instance output dir
        fuzzer_inst.append((sync_dir, []))
    else:
        # we're inside a multi instance sync dir
        for fdir in os.listdir(sync_dir):
            if os.path.isdir(os.path.join(sync_dir, fdir)):
                fuzzer_inst.append((fdir, []))

    if crash_dirs:
        fuzzer_inst = get_crash_directories(sync_dir, fuzzer_inst)
    else:
        fuzzer_inst = get_queue_directories(sync_dir, fuzzer_inst)

    return fuzzer_inst


def get_crash_directories(sync_dir, fuzzer_instances):
    for fi in fuzzer_instances:
        fuzz_dir = os.path.join(sync_dir, fi[0])
        for cdir in os.listdir(fuzz_dir):
            if os.path.isdir(os.path.join(fuzz_dir, cdir)) and global_crash_subdirs in cdir:
                fi[1].append(cdir)

    return fuzzer_instances


def get_queue_directories(sync_dir, fuzzer_instances):
    for fi in fuzzer_instances:
        fuzz_dir = os.path.join(sync_dir, fi[0])
        for qdir in os.listdir(fuzz_dir):
            if os.path.isdir(os.path.join(fuzz_dir, qdir)) and global_queue_subdirs in qdir:
                fi[1].append(qdir)

    return fuzzer_instances


def get_samples_from_dir(sample_subdir, abs_path=False):
    samples = []
    num_samples = 0
    for f in os.listdir(sample_subdir):
        if os.path.isfile(os.path.join(sample_subdir, f)) and f not in global_exclude_files:
            if abs_path:
                samples.append(os.path.join(sample_subdir, f))
            else:
                samples.append(f)
            num_samples += 1
    return num_samples, samples


def collect_samples(sync_dir, fuzzer_instances):
    samples = []
    num_samples = 0
    for fi in fuzzer_instances:
        fuzz_dir = os.path.join(sync_dir, fi[0])
        fuzz_samples = []

        for cd in fi[1]:
            tmp_num_samples, tmp_samples = get_samples_from_dir(os.path.join(fuzz_dir, cd))
            fuzz_samples.append((cd, sorted(tmp_samples)))
            num_samples += tmp_num_samples

        samples.append((fi[0], fuzz_samples))

    return num_samples, samples


def build_sample_index(sync_dir, out_dir, fuzzer_instances, db=None, min_filename=False, omit_fuzzer_name=False):
    sample_num, samples = collect_samples(sync_dir, fuzzer_instances)

    sample_index = SampleIndex.SampleIndex(out_dir, min_filename=min_filename, omit_fuzzer_name=omit_fuzzer_name)

    for fuzzer in samples:
        for sample_dir in fuzzer[1]:
            for sample in sample_dir[1]:
                sample_file = os.path.join(sync_dir, "%s/%s/%s" % (fuzzer[0], sample_dir[0], sample))
                sample_name = sample_index.__generate_output__(fuzzer[0], sample_file)

                if not db or not db.dataset_exists('Data', {'Sample': sample_name, 'Classification': '%',
                                                            'Classification_Description': '%',
                                                            'Hash': '%', 'User_Comment': '%'}, ['Sample']):
                    sample_index.add(fuzzer[0], sample_file)

    return sample_index


def copy_samples(sample_index):
    files_collected = []
    for sample in sample_index.index:
        dst_file = shutil.copyfile(sample['input'], os.path.join(sample_index.output_dir, sample['output']))
        files_collected.append(dst_file)

    return files_collected


def generate_sample_list(list_filename, files_collected):
    list_filename = os.path.abspath(os.path.expanduser(list_filename))

    try:
        fd = open(list_filename, "w")
        for f in files_collected:
            fd.writelines("%s\n" % f)

        fd.close()
    except (FileExistsError, PermissionError):
        print_err("Could not create file list '%s'!" % list_filename)

def stdin_mode(target_cmd):
    return not ("@@" in target_cmd)


def generate_gdb_exploitable_script(script_filename, sample_index, target_cmd, script_id=0, intermediate=False):
    target_cmd = target_cmd.split()
    gdb_target_binary = target_cmd[0]
    gdb_run_cmd = " ".join(target_cmd[1:])

    if not intermediate:
        script_filename = os.path.abspath(os.path.expanduser(script_filename))
        print_ok("Generating final gdb+exploitable script '%s' for %d samples..." % (script_filename,
                                                                                     len(sample_index.outputs())))
    else:
        script_filename = os.path.abspath(os.path.expanduser("%s.%d" % (script_filename, script_id)))
        print_ok("Generating intermediate gdb+exploitable script '%s' for %d samples..." %
                 (script_filename, len(sample_index.outputs())))

    gdb_exploitable_path = None
    gdbinit = os.path.expanduser("~/.gdbinit")
    if not os.path.exists(gdbinit) or b"exploitable.py" not in open(gdbinit, "rb").read():
        gdb_exploitable_path = os.path.join(exploitable.__path__[0], "exploitable.py")

    try:
        fd = open(script_filename, "w")

        # <script header>
        # source exploitable.py if necessary
        if gdb_exploitable_path:
            fd.writelines("source %s\n" % gdb_exploitable_path)

        # load executable
        fd.writelines("file %s\n" % gdb_target_binary)
        # </script_header>

        # fill script with content
        for f in sample_index.index:
            fd.writelines("echo Crash\ sample:\ '%s'\\n\n" % f['output'])

            if not stdin_mode(target_cmd):
                run_cmd = "run " + gdb_run_cmd + "\n"
            else:
                run_cmd = "run " + gdb_run_cmd + "< @@" + "\n"

            if intermediate:
                run_cmd = run_cmd.replace("@@", "'{}'".format(f['input']))
            else:
                run_cmd = run_cmd.replace("@@", os.path.join(sample_index.output_dir, "'{}'".format(f['output'])))

            fd.writelines(run_cmd)
            fd.writelines("exploitable\n")

        # <script_footer>
        fd.writelines("quit")
        # </script_footer>

        fd.close()
    except (FileExistsError, PermissionError):
        print_err("Could not open script file '%s' for writing!" % script_filename)


# ok, this needs improvement!!!
def execute_gdb_script(out_dir, script_filename, num_samples, num_threads):
    classification_data = []

    out_dir = os.path.expanduser(out_dir) + "/"

    grep_for = [
        "Crash sample: '",
        "Exploitability Classification: ",
        "Short description: ",
        "Hash: ",
        ]

    queue_list = []

    thread_list = []

    for n in range(0, num_threads, 1):
        script_args = [
            str(gdb_binary),
            "-x",
            str(os.path.join(out_dir, "%s.%d" % (script_filename, n))),
        ]

        out_queue = queue.Queue()
        out_queue_lock = threading.Lock()
        queue_list.append((out_queue, out_queue_lock))

        t = AflThread.GdbThread(n, script_args, out_dir, grep_for, out_queue, out_queue_lock)
        thread_list.append(t)
        print_ok("Executing gdb+exploitable script '%s.%d'..." % (script_filename, n))
        t.daemon = True
        t.start()

    for t in thread_list:
        t.join()

    grepped_output = []

    for q in queue_list:
        q[1].acquire()
        while not q[0].empty():
            grepped_output.append(q[0].get())
        q[1].release()

    i = 1
    print("*** GDB+EXPLOITABLE SCRIPT OUTPUT ***")
    for g in range(0, len(grepped_output)-len(grep_for)+1, len(grep_for)):
        if grepped_output[g+3] == "EXPLOITABLE":
            cex = clr.RED
            ccl = clr.BRI
        elif grepped_output[g+3] == "PROBABLY_EXPLOITABLE":
            cex = clr.YEL
            ccl = clr.BRI
        elif grepped_output[g+3] == "PROBABLY_NOT_EXPLOITABLE":
            cex = clr.BRN
            ccl = clr.RST
        elif grepped_output[g+3] == "NOT_EXPLOITABLE":
            cex = clr.GRN
            ccl = clr.GRA
        elif grepped_output[g+3] == "UNKNOWN":
            cex = clr.BLU
            ccl = clr.GRA
        else:
            cex = clr.GRA
            ccl = clr.GRA

        if len(grepped_output[g]) < 24:
            # Assume simplified sample file names,
            # so save some output space.
            ljust_width = 24
        else:
            ljust_width = 64
        print("%s[%05d]%s %s: %s%s%s %s[%s]%s" % (clr.GRA, i, clr.RST, grepped_output[g].ljust(ljust_width, '.'), cex,
                                                  grepped_output[g+3], clr.RST, ccl, grepped_output[g+1], clr.RST))
        classification_data.append({'Sample': grepped_output[g], 'Classification': grepped_output[g+3],
                                    'Classification_Description': grepped_output[g+1], 'Hash': grepped_output[g+2],
                                    'User_Comment': ''})
        i += 1

    if i > 1 and i < num_samples:
        print("%s[%05d]%s %s: %sINVALID SAMPLE (Aborting!)%s" % (clr.GRA, i, clr.RST,
                                                                 grepped_output[-1].ljust(ljust_width, '.'),
                                                                 clr.LRD, clr.RST))
        print(clr.LRD + "Returned data may be incomplete!" + clr.RST)
    print("*** ***************************** ***")

    # remove intermediate gdb scripts...
    for n in range(0, num_threads, 1):
        os.remove(os.path.join(out_dir, "%s.%d" % (script_filename, n)))

    return classification_data


def main(argv):
    show_info()
    check_gdb()

    parser = argparse.ArgumentParser(description="afl-collect copies all crash sample files from an afl sync dir used \
by multiple fuzzers when fuzzing in parallel into a single location providing easy access for further crash analysis.",
                                     usage="afl-collect [-d DATABASE] [-e|-g GDB_EXPL_SCRIPT_FILE] [-f LIST_FILENAME]\n \
[-h] [-j THREADS] [-m] [-r [-rt TIMEOUT]] [-rr] sync_dir collection_dir -- target_cmd")
    parser.add_argument("sync_dir", help="afl synchronisation directory crash samples will be collected from.")
    parser.add_argument("collection_dir",
                        help="Output directory that will hold a copy of all crash samples and other generated files. \
Existing files in the collection directory will be overwritten!")
    parser.add_argument("-d", "--database", dest="database_file", help="Submit sample data into an sqlite3 database (\
only when used together with '-e'). afl-collect skips processing of samples already found in existing database.",
                        default=None)
    parser.add_argument("-e", "--execute-gdb-script", dest="gdb_expl_script_file",
                        help="Generate and execute a gdb+exploitable script after crash sample collection for crash \
classification. (Like option '-g', plus script execution.)",
                        default=None)
    parser.add_argument("-f", "--filelist", dest="list_filename", default=None,
                        help="Writes all collected crash sample filenames into a file in the collection directory.")
    parser.add_argument("-g", "--generate-gdb-script", dest="gdb_script_file",
                        help="Generate gdb script to run 'exploitable.py' on all collected crash samples. Generated \
script will be placed into collection directory.", default=None)
    parser.add_argument("-j", "--threads", dest="num_threads", default=1,
                        help="Enable parallel analysis by specifying the number of threads afl-collect will utilize.")
    parser.add_argument("-m", "--minimize-filenames", dest="min_filename", action="store_const", const=True,
                        default=False, help="Minimize crash sample file names by only keeping fuzzer name and ID.")
    parser.add_argument("-r", "--remove-invalid", dest="remove_invalid", action="store_const", const=True,
                        default=False, help="Verify collected crash samples and remove samples that do not lead to \
crashes or cause timeouts (runs 'afl-vcrash.py -r' on collection directory). This step is done prior to any script \
file execution or file list generation.")
    parser.add_argument("-rr", "--remove-unexploitable", dest="remove_unexploitable", action="store_const", const=True,
                        default=False, help="Remove crash samples that have an exploitable classification of \
'NOT_EXPLOITABLE' or 'PROBABLY_NOT_EXPLOITABLE'. Sample file removal will take place after gdb+exploitable \
script execution. Has no effect without '-e'.")
    parser.add_argument("-rt", "--remove-timeout", dest="remove_timeout", default=10,
                        help="Specifies the maximum processing time in seconds for each sample during verification \
phase. Samples that cause the target to run longer are marked as timeouts and are removed from the index. Has no \
effect without '-r'.")
    parser.add_argument("target_cmd", nargs="+", help="Path to the target binary and its command line arguments. \
Use '@@' to specify crash sample input file position (see afl-fuzz usage).")

    args = parser.parse_args(argv[1:])

    sync_dir = os.path.abspath(os.path.expanduser(args.sync_dir))
    if not os.path.exists(sync_dir):
        print_err("No valid directory provided for <SYNC_DIR>!")
        return

    out_dir = os.path.abspath(os.path.expanduser(args.collection_dir))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    args.target_cmd = " ".join(args.target_cmd).split()
    args.target_cmd[0] = os.path.abspath(os.path.expanduser(args.target_cmd[0]))
    if not os.path.exists(args.target_cmd[0]):
        print_err("Target binary not found!")
        return
    args.target_cmd = " ".join(args.target_cmd)

    if args.database_file:
        db_file = os.path.abspath(os.path.expanduser(args.database_file))
    else:
        db_file = None

    print_ok("Going to collect crash samples from '%s'." % sync_dir)

    # initialize database
    if db_file:
        lite_db = con_sqlite.sqliteConnector(db_file)
        lite_db.init_database('Data', db_table_spec)
    else:
        lite_db = None

    fuzzers = get_fuzzer_instances(sync_dir)
    print_ok("Found %d fuzzers, collecting crash samples." % len(fuzzers))

    sample_index = build_sample_index(sync_dir, out_dir, fuzzers, lite_db, args.min_filename)

    if len(sample_index.index) > 0:
        print_ok("Successfully indexed %d crash samples." % len(sample_index.index))
    elif db_file:
        print_warn("No unseen samples found. Check your database for results!")
        return
    else:
        print_warn("No samples found. Check directory settings!")
        return

    if args.remove_invalid:
        from afl_utils import afl_vcrash
        invalid_samples, timeout_samples = afl_vcrash.verify_samples(int(args.num_threads), sample_index.inputs(),
                                                                     args.target_cmd, timeout_secs=float(args.remove_timeout))

        # store invalid samples in db
        if args.gdb_expl_script_file and db_file:
            print_ok("Saving invalid sample info to database.")
            for sample in invalid_samples:
                sample_name = sample_index.outputs(input_file=sample)
                dataset = {'Sample': sample_name[0], 'Classification': 'INVALID',
                           'Classification_Description': 'Sample does not cause a crash in the target.', 'Hash': '',
                           'User_Comment': ''}
                if not lite_db.dataset_exists('Data', dataset, ['Sample']):
                    lite_db.insert_dataset('Data', dataset)

            for sample in timeout_samples:
                sample_name = sample_index.outputs(input_file=sample)
                dataset = {'Sample': sample_name[0], 'Classification': 'TIMEOUT',
                           'Classification_Description': 'Sample caused a target execution timeout.', 'Hash': '',
                           'User_Comment': ''}
                if not lite_db.dataset_exists('Data', dataset, ['Sample']):
                    lite_db.insert_dataset('Data', dataset)

        # remove invalid samples from sample index
        sample_index.remove_inputs(invalid_samples+timeout_samples)
        print_warn("Removed %d invalid crash samples from index." % len(invalid_samples))
        print_warn("Removed %d timed out samples from index." % len(timeout_samples))

    # generate gdb+exploitable script
    if args.gdb_expl_script_file:
        divided_index = sample_index.divide(int(args.num_threads))

        for i in range(0, int(args.num_threads), 1):
            generate_gdb_exploitable_script(os.path.join(out_dir, args.gdb_expl_script_file), divided_index[i],
                                            args.target_cmd, i, intermediate=True)

        # execute gdb+exploitable script
        classification_data = execute_gdb_script(out_dir, args.gdb_expl_script_file, len(sample_index.inputs()),
                                                 int(args.num_threads))

        # Submit crash classification data into database
        if db_file:
            print_ok("Saving sample classification info to database.")
            for dataset in classification_data:
                if not lite_db.dataset_exists('Data', dataset, ['Sample']):
                    lite_db.insert_dataset('Data', dataset)

        # de-dupe by exploitable hash
        seen = set()
        seen_add = seen.add
        classification_data_dedupe = [x for x in classification_data
                                      if x['Hash'] not in seen and not seen_add(x['Hash'])]

        # remove dupe samples identified by exploitable hash
        uninteresting_samples = [x['Sample'] for x in classification_data
                                 if x not in classification_data_dedupe]

        sample_index.remove_outputs(uninteresting_samples)

        print_warn("Removed %d duplicate samples from index. Will continue with %d remaining samples." %
                   (len(uninteresting_samples), len(sample_index.index)))

        # remove crash samples that are classified uninteresting
        if args.remove_unexploitable:
            classification_unexploitable = [
                'NOT_EXPLOITABLE',
                'PROBABLY_NOT_EXPLOITABLE',
            ]

            uninteresting_samples = []

            for c in classification_data_dedupe:
                if c['Classification'] in classification_unexploitable:
                    uninteresting_samples.append(c['Sample'])

            sample_index.remove_outputs(uninteresting_samples)
            print_warn("Removed %d uninteresting crash samples from index." % len(uninteresting_samples))

        # generate output gdb script
        generate_gdb_exploitable_script(os.path.join(out_dir, args.gdb_expl_script_file), sample_index,
                                        args.target_cmd, 0)
    elif args.gdb_script_file:
        generate_gdb_exploitable_script(os.path.join(out_dir, args.gdb_script_file), sample_index, args.target_cmd)

    print_ok("Copying %d samples into output directory..." % len(sample_index.index))
    files_collected = copy_samples(sample_index)

    # generate filelist of collected crash samples
    if args.list_filename:
        generate_sample_list(os.path.abspath(os.path.expanduser(args.list_filename)), files_collected)
        print_ok("Generated crash sample list '%s'." % os.path.abspath(os.path.expanduser(args.list_filename)))

    # write db contents to file and close db connection
    if db_file:
        lite_db.commit_close()


if __name__ == "__main__":
    main(sys.argv)
