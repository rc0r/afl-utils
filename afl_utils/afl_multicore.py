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
try:
    import simplejson as json
except ImportError:
    import json
import os
import shutil
import signal
import subprocess
import sys
import time

import afl_utils
from afl_utils.AflPrettyPrint import print_err, print_ok, clr

afl_path = shutil.which("afl-fuzz")
if afl_path is None:
    print_err("afl-fuzz binary not found!")
    sys.exit(1)


def show_info():
    print(clr.CYA + "afl-multicore " + clr.BRI + "%s" % afl_utils.__version__ + clr.RST + " by %s" %
          afl_utils.__author__)
    print("Wrapper script to easily set up parallel fuzzing jobs.")
    print("")


def read_config(config_file):
    config_file = os.path.abspath(os.path.expanduser(config_file))

    if not os.path.isfile(config_file):
        print_err("Config file not found!")
        sys.exit(1)

    with open(config_file, "r") as f:
        config = json.load(f)

        if "session" not in config:
            config["session"] = "SESSION"

        return config


def afl_cmdline_from_config(config_settings, instance_number):
    afl_cmdline = []

    if "file" in config_settings:
        afl_cmdline.append("-f")
        if config_settings["file"] != "@@":
            afl_cmdline.append(config_settings["file"] + "_%03d" % instance_number)
        else:
            afl_cmdline.append(config_settings["file"])

    if "timeout" in config_settings:
        afl_cmdline.append("-t")
        afl_cmdline.append(config_settings["timeout"])

    if "mem_limit" in config_settings:
        afl_cmdline.append("-m")
        afl_cmdline.append(config_settings["mem_limit"])

    if "qemu" in config_settings and config_settings["qemu"]:
        afl_cmdline.append("-Q")

    if "dirty" in config_settings and config_settings["dirty"]:
        afl_cmdline.append("-d")

    if "dumb" in config_settings and config_settings["dumb"]:
        afl_cmdline.append("-n")

    if "dict" in config_settings:
        afl_cmdline.append("-x")
        afl_cmdline.append(config_settings["dict"])

    if "afl_margs" in config_settings:
        afl_cmdline.append(config_settings["afl_margs"])

    if "input" in config_settings:
        afl_cmdline.append("-i")
        afl_cmdline.append(config_settings["input"])

    if "output" in config_settings:
        afl_cmdline.append("-o")
        afl_cmdline.append(config_settings["output"])

    return afl_cmdline


def check_screen():
    inside_screen = False
    # try:
    #     screen_output = subprocess.check_output("screen -ls", shell=True, stderr=subprocess.DEVNULL,
    #                                             universal_newlines=True)
    # except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
    #     screen_output = e.output
    #
    # screen_output = screen_output.splitlines()
    #
    # for line in screen_output:
    #     if "(Attached)" in line:
    #         inside_screen = True

    if os.environ.get("STY"):
        inside_screen = True

    return inside_screen


def setup_screen_env(env_list):
    if len(env_list) > 0:
        # set environment variables in initializer window
        for env in env_list:
            env_tuple = env.split("=")
            screen_env_cmd = ["screen", "-X", "setenv", env_tuple[0], env_tuple[1]]
            subprocess.Popen(screen_env_cmd)

    # Set working directory for all newly
    # created screen windows to the directory
    # afl-multicore was executed from.
    cwd = os.getcwd()
    subprocess.Popen(["screen", "-X", "chdir", cwd])


def setup_screen(windows, env_list):
    setup_screen_env(env_list)

    # create number of windows
    for i in range(0, windows, 1):
        subprocess.Popen(["screen"])

    # go back to 1st window
    subprocess.Popen("screen -X select 0".split())


def sigint_handler(signal, frame):
    print()
    print_ok("Test run aborted by user!")
    sys.exit(0)


def build_target_cmd(conf_settings):
    target_cmd = [conf_settings["target"], conf_settings["cmdline"]]
    target_cmd = " ".join(target_cmd).split()
    target_cmd[0] = os.path.abspath(os.path.expanduser(target_cmd[0]))
    if not os.path.exists(target_cmd[0]):
        print_err("Target binary not found!")
        sys.exit(1)
    target_cmd = " ".join(target_cmd)
    return target_cmd


def build_master_cmd(conf_settings, target_cmd):
    # If afl -f file switch was used, automatically use correct input
    # file for master instance.
    if "%%" in target_cmd:
        target_cmd = target_cmd.replace("%%", conf_settings["file"] + "_000")
    # compile command-line for master
    # $ afl-fuzz -i <input_dir> -o <output_dir> -M <session_name>.000 <afl_args> \
    #   </path/to/target.bin> <target_args>
    master_cmd = [afl_path] + afl_cmdline_from_config(conf_settings, 0)
    master_cmd += ["-M", "%s000" % conf_settings["session"], "--", target_cmd]
    master_cmd = " ".join(master_cmd)
    return master_cmd


def build_slave_cmd(conf_settings, slave_num, target_cmd):
    # If afl -f file switch was used, automatically use correct input
    # file for slave instance.
    if "%%" in target_cmd:
        target_cmd = target_cmd.replace("%%", conf_settings["file"] + "_%03d" % slave_num)
    # compile command-line for slaves
    # $ afl-fuzz -i <input_dir> -o <output_dir> -S <session_name>.NNN <afl_args> \
    #   </path/to/target.bin> <target_args>
    slave_cmd = [afl_path] + afl_cmdline_from_config(conf_settings, slave_num)
    slave_cmd += ["-S", "%s%03d" % (conf_settings["session"], slave_num), "--", target_cmd]
    slave_cmd = " ".join(slave_cmd)
    return slave_cmd


def write_pgid_file(conf_settings):
    print("")
    if not conf_settings["interactive"]:
        # write/append PGID to file /tmp/afl-multicore.PGID.<SESSION>
        f = open("/tmp/afl_multicore.PGID.%s" % conf_settings["session"], "a")
        if f.writable():
            f.write("%d\n" % os.getpgid(0))
        f.close()
        print_ok("For progress info check: %s/%sxxx/fuzzer_stats!" % (conf_settings["output"],
                                                                      conf_settings["session"]))
    else:
        print_ok("Check the newly created screen windows!")


def get_slave_count(command, conf_settings):
    if command == "add":
        slave_start = 0
        slave_off = 0
        dirs = os.listdir(conf_settings["output"])
        for d in dirs:
            if os.path.isdir(os.path.abspath(os.path.join(conf_settings["output"], d))) \
                    and conf_settings["session"] in d:
                slave_start += 1
        conf_settings["slave_only"] = True
    else:
        slave_start = 1
        slave_off = 1
    return slave_off, slave_start


def get_job_counts(jobs_arg):
    if isinstance(jobs_arg, str) and "," in jobs_arg:
        jobs_arg = jobs_arg.split(",")
        num_jobs = int(jobs_arg[0])
        jobs_offset = int(jobs_arg[1])
    else:
        num_jobs = int(jobs_arg)
        jobs_offset = 0
    return (num_jobs, jobs_offset)


def has_master(conf_settings, jobs_offset):
    if jobs_offset <= 0:
        return "slave_only" not in conf_settings or ("slave_only" in conf_settings and not conf_settings["slave_only"])
    else:
        return False


def startup_delay(conf_settings, instance_num, command, startup_delay):
    if startup_delay is not None:
        if startup_delay == "auto":
            if command == "resume":
                delay = auto_startup_delay(conf_settings, instance_num)
            else:
                delay = auto_startup_delay(conf_settings, 0, resume=False)
        else:
            delay = int(startup_delay)

        time.sleep(delay)
        return delay


def auto_startup_delay(config_settings, instance_num, resume=True):
    # Worst case startup time (t_sw) per fuzzer (N - number of samples, T - max. timeout):
    #   t_sw = N * T
    # Optimized case startup time (t_sa) per fuzzer (O - optimization factor):
    #   t_sa = O * t_sw = O * N * T
    # Educated guess for some O:
    #    O = 1 / sqrt(N)
    # This might need some tuning!
    if resume:
        instance_dir = os.path.join(config_settings["output"], "{}{:03d}".format(config_settings["session"], instance_num),
                                    "queue")
    else:
        instance_dir = config_settings["input"]
    sample_list = os.listdir(instance_dir)
    N = len(sample_list)
    T = float(config_settings["timeout"].strip(" +")) if "timeout" in config_settings else 1000.0
    O = N**(-1/2)

    return O * T * N / 1000


def main(argv):
    show_info()

    parser = argparse.ArgumentParser(description="afl-multicore starts several parallel fuzzing jobs, that are run \
in the background. For fuzzer stats see 'out_dir/SESSION###/fuzzer_stats'!",
                                     usage="afl-multicore [-c config] [-h] [-s secs] [-t] [-v] <cmd> <jobs[,offset]>")

    parser.add_argument("-c", "--config", dest="config_file",
                        help="afl-multicore config file (Default: afl-multicore.conf)!", default="afl-multicore.conf")
    parser.add_argument("-s", "--startup-delay", dest="startup_delay", default=None, help="Wait a configurable  amount \
of time after starting/resuming each afl instance to avoid interference during fuzzer startup. Provide wait time in \
seconds.")
    parser.add_argument("-t", "--test", dest="test_run", action="store_const", const=True, default=False, help="Perform \
a test run by starting a single afl instance in interactive mode using a test output directory.")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_const", const=True,
                        default=False, help="For debugging purposes do not redirect stderr/stdout of the created \
subprocesses to /dev/null (Default: off). Check 'nohup.out' for further outputs.")
    parser.add_argument("cmd", help="afl-multicore command to execute: start, resume, add.")
    parser.add_argument("jobs", help="Number of instances to start/resume/add. For resumes you may specify an optional \
job offset that allows to resume specific (ranges of) afl-instances.")

    args = parser.parse_args(argv[1:])

    conf_settings = read_config(os.path.abspath(os.path.expanduser(args.config_file)))

    if args.test_run:
        signal.signal(signal.SIGINT, sigint_handler)
        conf_settings["output"] += "_test"
        conf_settings["interactive"] = False
        args.jobs = 1
        args.cmd = "start"

    jobs_count, jobs_offset = get_job_counts(args.jobs)
    if args.cmd != "resume":
        conf_settings["input"] = os.path.abspath(os.path.expanduser(conf_settings["input"]))
        if not os.path.exists(conf_settings["input"]):
            print_err("No valid directory provided for <INPUT_DIR>!")
            sys.exit(1)
        jobs_offset = 0
    else:
        conf_settings["input"] = "-"

    conf_settings["output"] = os.path.abspath(os.path.expanduser(conf_settings["output"]))

    slave_off, slave_start = get_slave_count(args.cmd, conf_settings)

    if "interactive" in conf_settings and conf_settings["interactive"]:
        if not check_screen():
            print_err("When using screen mode, please run afl-multicore from inside a screen session!")
            sys.exit(1)

        if "environment" in conf_settings:
            setup_screen(jobs_count, conf_settings["environment"])
        else:
            setup_screen(jobs_count, [])

    target_cmd = build_target_cmd(conf_settings)
    master_cmd = build_master_cmd(conf_settings, target_cmd)

    if args.test_run:
        with subprocess.Popen(master_cmd.split()) as test_proc:
            print_ok("Test instance started (PID: %d)" % test_proc.pid)

    if has_master(conf_settings, jobs_offset):
        print_ok("Starting master instance...")

        if "interactive" in conf_settings and conf_settings["interactive"]:
            subprocess.Popen("screen -X select 1".split())
            screen_cmd = ["screen", "-X", "eval", "exec %s" % master_cmd, "next"]
            subprocess.Popen(screen_cmd)
            print(" Master 000 started inside new screen window")
        else:
            if not args.verbose:
                master = subprocess.Popen(" ".join(['nohup', master_cmd]).split(), stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
            else:
                master = subprocess.Popen(" ".join(['nohup', master_cmd]).split())
            print(" Master 000 started (PID: %d)" % master.pid)

        startup_delay(conf_settings, 0, args.cmd, args.startup_delay)

    print_ok("Starting slave instances...")
    num_slaves = jobs_count+slave_start-slave_off
    slave_start += (jobs_offset-1)
    num_slaves += jobs_offset
    for i in range(slave_start, num_slaves, 1):
        slave_cmd = build_slave_cmd(conf_settings, i, target_cmd)

        if "interactive" in conf_settings and conf_settings["interactive"]:
            subprocess.Popen(["screen", "-X", "select", "%d" % (i + 1)])
            screen_cmd = ["screen", "-X", "eval", "exec %s" % slave_cmd, "next"]
            subprocess.Popen(screen_cmd)
            print(" Slave %03d started inside new screen window" % i)
        else:
            if not args.verbose:
                slave = subprocess.Popen(" ".join(['nohup', slave_cmd]).split(), stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)
            else:
                slave = subprocess.Popen(" ".join(['nohup', slave_cmd]).split())
            print(" Slave %03d started (PID: %d)" % (i, slave.pid))

        if i < (num_slaves-1):
            startup_delay(conf_settings, i, args.cmd, args.startup_delay)

    write_pgid_file(conf_settings)


if __name__ == "__main__":
    main(sys.argv)
