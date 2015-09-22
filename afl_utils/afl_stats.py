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
from configparser import ConfigParser, NoOptionError, NoSectionError, MissingSectionHeaderError
import os
import sys
import socket
import time
import twitter
from urllib.error import URLError

import afl_utils
from afl_utils.colors import clr


config_interval = 30
config_twitter_consumer_key = None
config_twitter_consumer_secret = None
config_twitter_creds_file = ".afl-stats.creds"
config_fuzz_directories = []


def show_info():
    print(clr.CYA + "afl-stats " + clr.BRI + "%s" % afl_utils.__version__ + clr.RST + " by %s" % afl_utils.__author__)
    print("Send stats of afl-fuzz jobs to Twitter.")
    print("")


def read_config(config_file):
    try:
        config_file = os.path.abspath(os.path.expanduser(config_file))

        if not os.path.isfile(config_file):
            print("Error: Config file not found!")
            sys.exit(1)

        config = ConfigParser()
        config.read(config_file)
    except (MissingSectionHeaderError, UnicodeDecodeError):
        print("Error: No valid configuration file specified!")
        sys.exit(1)

    try:
        global config_interval, config_twitter_consumer_key, config_twitter_consumer_secret, config_twitter_creds_file
        config_interval = config.get("core", "interval", raw=True)
        config_twitter_consumer_key = config.get("twitter", "consumer_key", raw=True)
        config_twitter_consumer_secret = config.get("twitter", "consumer_secret", raw=True)
        config_twitter_creds_file = config.get("twitter", "credentials_file", raw=True)
        config_twitter_creds_file = os.path.abspath(os.path.expanduser(config_twitter_creds_file))
    except NoOptionError as e:
        print("Error: No valid configuration file specified! Option '%s.%s' not found!" % (e.section, e.option))
        sys.exit(1)
    except NoSectionError as e:
        print("Error: No valid configuration file specified! Section '%s' not found!" % e.section)
        sys.exit(1)

    exists = True
    i = 0
    while exists:
        try:
            config_fuzz_directories.append(config.get("fuzzers", str(i), raw=True))
            i += 1
        except NoOptionError:
            exists = False


def twitter_init():
    try:
        global config_interval, config_twitter_consumer_key, config_twitter_consumer_secret, config_twitter_creds_file

        if not os.path.exists(config_twitter_creds_file):
            twitter.oauth_dance("fuzzer_stats", config_twitter_consumer_key, config_twitter_consumer_secret,
                                config_twitter_creds_file)
        oauth_token, oauth_secret = twitter.read_token_file(config_twitter_creds_file)
        twitter_instance = twitter.Twitter(auth=twitter.OAuth(oauth_token, oauth_secret, config_twitter_consumer_key,
                                                              config_twitter_consumer_secret))
        return twitter_instance
    except (twitter.TwitterHTTPError, URLError):
        print("Network error, twitter login failed! Check your connection!")
        sys.exit(1)


def fuzzer_alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return 0
    return 1


def parse_stat_file(stat_file):
    try:
        f = open(stat_file, "r")
        lines = f.readlines()

        stats = {
            'fuzzer_pid': None,
            'execs_done': None,
            'execs_per_sec': None,
            'paths_total': None,
            'paths_favored': None,
            'pending_favs': None,
            'pending_total': None,
            'unique_crashes': None,
            'unique_hangs': None,
            'afl_banner': None
        }

        for l in lines:
            for k in stats.keys():
                if k != "fuzzer_pid":
                    if k in l:
                        stats[k] = l[16:].strip(" \r\n")
                else:
                    if k in l:
                        stats[k] = fuzzer_alive(int(l[16:].strip(" \r\n")))

        return stats
    except FileNotFoundError as e:
        print("Error: Stat file '%s' not found!" % e.filename)

    return None


def load_stats(fuzzer_dir):
    fuzzer_dir = os.path.abspath(os.path.expanduser(fuzzer_dir))

    if not os.path.isdir(fuzzer_dir):
        print("Invalid fuzzing directory specified ('%s')." % fuzzer_dir)
        return None

    fuzzer_stats = []

    if os.path.isfile(os.path.join(fuzzer_dir, "fuzzer_stats")):
        # single afl-fuzz job
        stats = parse_stat_file(os.path.join(fuzzer_dir, "fuzzer_stats"))
        if stats:
            fuzzer_stats.append(stats)
    else:
        fuzzer_inst = []
        for fdir in os.listdir(fuzzer_dir):
            if os.path.isdir(os.path.join(fuzzer_dir, fdir)):
                fuzzer_inst.append(os.path.join(fuzzer_dir, fdir, "fuzzer_stats"))

        for stat_file in fuzzer_inst:
            stats = parse_stat_file(stat_file)
            if stats:
                fuzzer_stats.append(stats)

    return fuzzer_stats


def summarize_stats(stats):
    sum_stat = {
            'fuzzers': len(stats),
            'fuzzer_pid': 0,
            'execs_done': 0,
            'execs_per_sec': 0,
            'paths_total': 0,
            'paths_favored': 0,
            'pending_favs': 0,
            'pending_total': 0,
            'unique_crashes': 0,
            'unique_hangs': 0,
            'afl_banner': 0,
            'host': socket.gethostname()
        }

    for s in stats:
        for k in sum_stat.keys():
            if k in s.keys():
                if k != "afl_banner":
                    sum_stat[k] += float(s[k])
                else:
                    sum_stat[k] = s[k][:15]

    return sum_stat


def prettify_stat(_stat, console=True):
    _stat = _stat.copy()
    _stat['execs_done'] /= 1e6
    if console:
        _stat['afl_banner'] = clr.BLU + _stat['afl_banner'] + clr.RST
        _stat['host'] = clr.LBL + _stat['host'] + clr.RST

        lbl = clr.GRA
        if _stat['fuzzer_pid'] == 0:
            alc = clr.LRD
        else:
            alc = clr.LGN if _stat['fuzzer_pid'] == _stat['fuzzers'] else clr.YEL
        clc = clr.MGN if _stat['unique_crashes'] == 0 else clr.LRD
        rst = clr.RST
        pretty_stat =\
            "[%s on %s]\n %sAlive:%s   %s%d/%d%s\n %sExecs:%s   %d m\n %sSpeed:%s   %.1f x/s\n %sPend:%s    %d/%d\n" \
            " %sCrashes:%s %s%d%s\n" % (_stat['afl_banner'], _stat['host'], lbl, rst, alc, _stat['fuzzer_pid'],
                                        _stat['fuzzers'], rst, lbl, rst, _stat['execs_done'], lbl, rst,
                                        _stat['execs_per_sec'], lbl, rst, _stat['pending_total'],
                                        _stat['pending_favs'], lbl, rst, clc, _stat['unique_crashes'], rst)
    else:
        pretty_stat = "[%s on %s]\nAlive: %d/%d\nExecs: %d m\nSpeed: %.1f x/s\nPend: %d/%d\nCrashes: %d" %\
                      (_stat['afl_banner'], _stat['host'], _stat['fuzzer_pid'], _stat['fuzzers'], _stat['execs_done'],
                       _stat['execs_per_sec'], _stat['pending_total'], _stat['pending_favs'], _stat['unique_crashes'])
    return pretty_stat


def main(argv):
    show_info()

    parser = argparse.ArgumentParser(description="Post selected contents of fuzzer_stats to Twitter.",
                                     usage="afl-stats [-c]\n")

    parser.add_argument("-c", "--config", dest="config_file",
                        help="afl-stats config file (Default: afl-stats.conf)!", default="afl-stats.conf")

    args = parser.parse_args(argv[1:])

    read_config(args.config_file)

    twitter_inst = twitter_init()

    doExit = False
    while not doExit:
        for fuzzer in config_fuzz_directories:
            stats = load_stats(fuzzer)
            sum_stats = summarize_stats(stats)

            print(prettify_stat(sum_stats, True))

            tweet = prettify_stat(sum_stats, False)

            l = len(tweet)
            c = clr.LRD if l>140 else clr.LGN
            print("[" + clr.LGN + "+" + clr.RST + "] Tweeting status (%s%d" % (c, l) + clr.RST + " chars)...")
            print()

            twitter_inst.statuses.update(status=tweet)

        if int(config_interval) < 0:
            doExit = True
        else:
            time.sleep(config_interval*60)


if __name__ == "__main__":
    main(sys.argv)
