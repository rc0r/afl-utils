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
from configparser import ConfigParser, NoOptionError, NoSectionError, MissingSectionHeaderError

import afl_utils
from afl_utils.AflPrettyPrint import print_err, print_ok, clr

# afl-multicore global settings
afl_path = "afl-fuzz"   # in PATH


def show_info():
    print(clr.CYA + "afl-multicore " + clr.BRI + "%s" % afl_utils.__version__ + clr.RST + " by %s" %
          afl_utils.__author__)
    print("Wrapper script to easily set up parallel fuzzing jobs.")
    print("")


def read_config(config_file):
    try:
        config_file = os.path.abspath(os.path.expanduser(config_file))

        if not os.path.isfile(config_file):
            print_err("Config file not found!")
            sys.exit(1)

        config = ConfigParser()
        # overwrite optionxform to not convert config file items to lower case
        config.optionxform = str
        config.read(config_file)
    except (MissingSectionHeaderError, UnicodeDecodeError):
        print_err("No valid configuration file specified!")
        sys.exit(1)

    try:
        conf_settings = dict()

        # Get required settings
        conf_settings["input"] = config.get("afl.dirs", "input", raw=True)
        conf_settings["output"] = config.get("afl.dirs", "output", raw=True)

        conf_settings["target"] = config.get("target", "target", raw=True)
        conf_settings["cmdline"] = config.get("target", "cmdline", raw=True)

        # Get optional settings
        if config.has_option("afl.ctrl", "file"):
            conf_settings["file"] = config.get("afl.ctrl", "file", raw=True)
        else:
            conf_settings["file"] = None

        if config.has_option("afl.ctrl", "timeout"):
            conf_settings["timeout"] = config.get("afl.ctrl", "timeout", raw=True)
        else:
            conf_settings["timeout"] = None

        if config.has_option("afl.ctrl", "afl_margs"):
            conf_settings["afl_margs"] = config.get("afl.ctrl", "afl_margs", raw=True)
        else:
            conf_settings["afl_margs"] = None

        if config.has_option("afl.ctrl", "mem_limit"):
            conf_settings["mem_limit"] = config.get("afl.ctrl", "mem_limit", raw=True)
        else:
            conf_settings["mem_limit"] = None

        if config.has_option("afl.ctrl", "qemu"):
            conf_settings["qemu"] = config.get("afl.ctrl", "qemu", raw=True)
        else:
            conf_settings["qemu"] = None

        if config.has_option("afl.behavior", "dirty"):
            conf_settings["dirty"] = config.get("afl.behavior", "dirty", raw=True)
        else:
            conf_settings["dirty"] = None

        if config.has_option("afl.behavior", "dumb"):
            conf_settings["dumb"] = config.get("afl.behavior", "dumb", raw=True)
        else:
            conf_settings["dumb"] = None

        if config.has_option("afl.behavior", "dict"):
            conf_settings["dict"] = config.get("afl.behavior", "dict", raw=True)
        else:
            conf_settings["dict"] = None

        if config.has_option("job", "session"):
            conf_settings["session"] = config.get("job", "session", raw=True)
        else:
            conf_settings["session"] = "SESSION"

        if config.has_option("job", "slave_only"):
            if config.get("job", "slave_only", raw=True) == "on":
                conf_settings["slave_only"] = True
            else:
                conf_settings["slave_only"] = False
        else:
            conf_settings["slave_only"] = False

        if config.has_option("job", "interactive"):
            if config.get("job", "interactive", raw=True) == "on":
                conf_settings["interactive"] = True
            else:
                conf_settings["interactive"] = False
        else:
            conf_settings["interactive"] = False

        if config.has_section("environment"):
            environment = []
            env_list = config.options("environment")
            for env in env_list:
                environment.append((env, config.get("environment", env, raw=True)))
        else:
            environment = None
    except NoOptionError as e:
        print_err("No valid configuration file specified! Option '" + clr.GRA + "%s.%s" % (e.section, e.option) +
                  clr.RST + "' not found!")
        sys.exit(1)
    except NoSectionError as e:
        print_err("No valid configuration file specified! Section '" + clr.GRA + "%s" % e.section + clr.RST +
                  "' not found!")
        sys.exit(1)

    return conf_settings, environment


def afl_cmdline_from_config(config_settings):
    afl_cmdline = []

    if config_settings["file"]:
        afl_cmdline.append("-f")
        afl_cmdline.append(config_settings["file"])

    if config_settings["timeout"]:
        afl_cmdline.append("-t")
        afl_cmdline.append(config_settings["timeout"])

    if config_settings["mem_limit"]:
        afl_cmdline.append("-m")
        afl_cmdline.append(config_settings["mem_limit"])

    if config_settings["qemu"] == "on":
        afl_cmdline.append("-Q")

    if config_settings["dirty"] == "on":
        afl_cmdline.append("-d")

    if config_settings["dumb"] == "on":
        afl_cmdline.append("-n")

    if config_settings["dict"]:
        afl_cmdline.append("-x")
        afl_cmdline.append(config_settings["dict"])

    if config_settings["afl_margs"]:
        afl_cmdline.append(config_settings["afl_margs"])

    if config_settings["input"]:
        afl_cmdline.append("-i")
        afl_cmdline.append(config_settings["input"])

    if config_settings["output"]:
        afl_cmdline.append("-o")
        afl_cmdline.append(config_settings["output"])

    return afl_cmdline


def check_session(session):
    session_active = os.path.isfile("/tmp/afl_multicore.PGID.%s" % session)

    if session_active:
        print("It seems you're already running an afl-multicore session with name '%s'." % session)
        print("Please choose another session name using '-S <session>'!")
        print("")
        print("If you're sure there is no active session with name '%s'," % session)
        print("you may delete the PGID file '/tmp/afl_multicore.PGID.%s'." % session)
        print("")
        print("To avoid this message in the future please abort active afl-multicore")
        print("sessions using 'afl-multikill -S <session>'!")

    return not session_active


def check_screen():
    inside_screen = False
    try:
        screen_output = subprocess.check_output("screen -ls", shell=True, stderr=subprocess.DEVNULL,
                                                universal_newlines=True)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        screen_output = e.output

    screen_output = screen_output.splitlines()

    for line in screen_output:
        if "(Attached)" in line:
            inside_screen = True

    return inside_screen


def setup_screen_env(env_list):
    if env_list:
        # set environment variables in initializer window
        for env_tuple in env_list:
            screen_env_cmd = ["screen", "-X", "setenv", env_tuple[0], env_tuple[1]]
            subprocess.Popen(screen_env_cmd)


def setup_screen(windows, env_list):
    setup_screen_env(env_list)

    # create number of windows
    for i in range(0, windows, 1):
        subprocess.Popen(["screen"])

    # go back to 1st window
    subprocess.Popen("screen -X select 0".split())


def main(argv):
    show_info()

    parser = argparse.ArgumentParser(description="afl-multicore starts several parallel fuzzing jobs, that are run \
in the background. For fuzzer stats see 'out_dir/SESSION###/fuzzer_stats'!",
                                     usage="afl-multicore [-c config] [-h] [-v] <cmd> <jobs>")

    parser.add_argument("-c", "--config", dest="config_file",
                        help="afl-multicore config file (Default: afl-multicore.conf)!", default="afl-multicore.conf")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_const", const=True,
                        default=False, help="For debugging purposes do not redirect stderr/stdout of the created \
subprocesses to /dev/null (Default: off). Check 'nohup.out' for further outputs.")
    parser.add_argument("cmd", help="afl-multicore command to execute: start, resume, add.")
    parser.add_argument("jobs", help="Number of instances to start/resume/add.")

    args = parser.parse_args(argv[1:])

    conf_settings, environment = read_config(os.path.abspath(os.path.expanduser(args.config_file)))

    # if not check_session(conf_settings["session"]):
    #     return

    if args.cmd != "resume":
        conf_settings["input"] = os.path.abspath(os.path.expanduser(conf_settings["input"]))
        if not os.path.exists(conf_settings["input"]):
            print_err("No valid directory provided for <INPUT_DIR>!")
            return
    else:
        conf_settings["input"] = "-"

    conf_settings["output"] = os.path.abspath(os.path.expanduser(conf_settings["output"]))

    if args.cmd == "add":
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

    target_cmd = [conf_settings["target"], conf_settings["cmdline"]]
    target_cmd = " ".join(target_cmd).split()
    target_cmd[0] = os.path.abspath(os.path.expanduser(target_cmd[0]))
    if not os.path.exists(target_cmd[0]):
        print_err("Target binary not found!")
        return
    target_cmd = " ".join(target_cmd)

    if conf_settings["interactive"]:
        if not check_screen():
            print_err("When using screen mode, please run afl-multicore from inside a screen session!")
            return

        setup_screen(int(args.jobs), environment)

    if not conf_settings["slave_only"]:
        # compile command-line for master
        # $ afl-fuzz -i <input_dir> -o <output_dir> -M <session_name>.000 <afl_args> \
        #   </path/to/target.bin> <target_args>
        master_cmd = [afl_path] + afl_cmdline_from_config(conf_settings)
        master_cmd += ["-M", "%s000" % conf_settings["session"], "--", target_cmd]
        master_cmd = " ".join(master_cmd)
        print_ok("Starting master instance...")

        if not conf_settings["interactive"]:
            if not args.verbose:
                master = subprocess.Popen(" ".join(['nohup', master_cmd]).split(), stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
            else:
                master = subprocess.Popen(" ".join(['nohup', master_cmd]).split())
            print(" Master 000 started (PID: %d)" % master.pid)
        else:
            subprocess.Popen("screen -X select 1".split())
            screen_cmd = ["screen", "-X", "eval", "exec %s" % master_cmd, "next"]
            subprocess.Popen(screen_cmd)
            print(" Master 000 started inside new screen window")

    # compile command-line for slaves
    print_ok("Starting slave instances...")
    for i in range(slave_start, int(args.jobs)+slave_start-slave_off, 1):
        # $ afl-fuzz -i <input_dir> -o <output_dir> -S <session_name>.NNN <afl_args> \
        #   </path/to/target.bin> <target_args>
        slave_cmd = [afl_path] + afl_cmdline_from_config(conf_settings)
        slave_cmd += ["-S", "%s%03d" % (conf_settings["session"], i), "--", target_cmd]
        slave_cmd = " ".join(slave_cmd)

        if not conf_settings["interactive"]:
            if not args.verbose:
                slave = subprocess.Popen(" ".join(['nohup', slave_cmd]).split(), stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)
            else:
                slave = subprocess.Popen(" ".join(['nohup', slave_cmd]).split())
            print(" Slave %03d started (PID: %d)" % (i, slave.pid))
        else:
            subprocess.Popen(["screen", "-X", "select", "%d" % (i+1)])
            screen_cmd = ["screen", "-X", "eval", "exec %s" % slave_cmd, "next"]
            subprocess.Popen(screen_cmd)
            print(" Slave %03d started inside new screen window" % i)

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


if __name__ == "__main__":
    main(sys.argv)
