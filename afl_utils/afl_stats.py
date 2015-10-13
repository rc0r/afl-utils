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
from afl_utils.AflPrettyPrint import *


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
            print_err("Config file not found!")
            sys.exit(1)

        config = ConfigParser()
        config.read(config_file)
    except (MissingSectionHeaderError, UnicodeDecodeError):
        print_err("No valid configuration file specified!")
        sys.exit(1)

    try:
        global config_interval, config_twitter_consumer_key, config_twitter_consumer_secret, config_twitter_creds_file
        config_interval = config.get("core", "interval", raw=True)
        config_twitter_consumer_key = config.get("twitter", "consumer_key", raw=True)
        config_twitter_consumer_secret = config.get("twitter", "consumer_secret", raw=True)
        config_twitter_creds_file = config.get("twitter", "credentials_file", raw=True)
        config_twitter_creds_file = os.path.abspath(os.path.expanduser(config_twitter_creds_file))
    except NoOptionError as e:
        print_err("No valid configuration file specified! Option '" + clr.GRA + "%s.%s" % (e.section, e.option) +
                  clr.RST + "' not found!")
        sys.exit(1)
    except NoSectionError as e:
        print_err("No valid configuration file specified! Section '" + clr.GRA + "%s" % e.section + clr.RST +
                  "' not found!")
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
        print_err("Network error, twitter login failed! Check your connection!")
        sys.exit(1)


def shorten_tweet(tweet):
    if len(tweet) > 140:
        print_ok("Status too long, will be shortened to 140 chars!")
        short_tweet = tweet[:137] + "..."
    else:
        short_tweet = tweet
    return short_tweet


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
        print_warn("Stat file " + clr.GRA + "%s" % e.filename + clr.RST + "not found!")

    return None


def load_stats(fuzzer_dir):
    fuzzer_dir = os.path.abspath(os.path.expanduser(fuzzer_dir))

    if not os.path.isdir(fuzzer_dir):
        print_warn("Invalid fuzzing directory specified: " + clr.GRA + "%s" % fuzzer_dir + clr.RST)
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
            'host': socket.gethostname()[:10]
        }

    for s in stats:
        for k in sum_stat.keys():
            if k in s.keys():
                if k != "afl_banner":
                    sum_stat[k] += float(s[k])
                else:
                    sum_stat[k] = s[k][:10]

    return sum_stat


def diff_stats(sum_stats, old_stats):
    if len(sum_stats) != len(old_stats):
        print_warn("Stats corrupted for '" + clr.GRA + "%s" % sum_stats['afl_banner'] + clr.RST + "'!")
        return None

    diff_stat = {
            'fuzzers': len(sum_stats),
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
            'host': socket.gethostname()[:10]
        }

    for k in sum_stats.keys():
        if k not in ['afl_banner', 'host']:
            diff_stat[k] = sum_stats[k] - old_stats[k]
        else:
            diff_stat[k] = sum_stats[k]

    return diff_stat


def prettify_stat(stat, dstat, console=True):
    _stat = stat.copy()
    _dstat = dstat.copy()
    _stat['execs_done'] /= 1e6
    _dstat['execs_done'] /= 1e6

    if _dstat['fuzzer_pid'] == _dstat['fuzzers'] == 0:
        ds_alive = ""
    else:
        ds_alive = " (%+d/%+d)" % (_dstat['fuzzer_pid'], _dstat['fuzzers'])

    if int(_dstat['execs_done']) == 0:
        ds_exec = " "
    else:
        ds_exec = " (%+d) " % _dstat['execs_done']

    if _dstat['execs_per_sec'] == 0:
        ds_speed = " "
    else:
        ds_speed = " (%+1.f) " % _dstat['execs_per_sec']

    if _dstat['pending_total'] == _dstat['pending_favs'] == 0:
        ds_pend = ""
    else:
        ds_pend = " (%+d/%+d)" % (_dstat['pending_total'], _dstat['pending_favs'])

    if _dstat['unique_crashes'] == 0:
        ds_crash = ""
    else:
        ds_crash = " (%+d)" % _dstat['unique_crashes']

    if console:
        # colorize stats
        _stat['afl_banner'] = clr.BLU + _stat['afl_banner'] + clr.RST
        _stat['host'] = clr.LBL + _stat['host'] + clr.RST

        lbl = clr.GRA
        if _stat['fuzzer_pid'] == 0:
            alc = clr.LRD
            slc = clr.GRA
        else:
            alc = clr.LGN if _stat['fuzzer_pid'] == _stat['fuzzers'] else clr.YEL
            slc = ""
        clc = clr.MGN if _stat['unique_crashes'] == 0 else clr.LRD
        rst = clr.RST

        # colorize diffs
        if _dstat['fuzzer_pid'] < 0 or _dstat['fuzzers'] < 0:
            ds_alive = clr.RED + ds_alive + clr.RST
        else:
            ds_alive = clr.GRN + ds_alive + clr.RST

        if int(_dstat['execs_done']) < 0:
            ds_exec = clr.RED + ds_exec + clr.RST
        else:
            ds_exec = clr.GRN + ds_exec + clr.RST

        if _dstat['execs_per_sec'] < 0:
            ds_speed = clr.RED + ds_speed + clr.RST
        else:
            ds_speed = clr.GRN + ds_speed + clr.RST

        if _dstat['unique_crashes'] < 0:
            ds_crash = clr.RED + ds_crash + clr.RST
        else:
            ds_crash = clr.GRN + ds_crash + clr.RST

        ds_pend = clr.GRA + ds_pend + clr.RST

        pretty_stat =\
            "[%s on %s]\n %sAlive:%s   %s%d/%d%s%s\n %sExecs:%s   %d%sm\n %sSpeed:%s   %s%.1f%sx/s%s\n %sPend:%s    %d/%d%s\n" \
            " %sCrashes:%s %s%d%s%s" % (_stat['afl_banner'], _stat['host'], lbl, rst, alc, _stat['fuzzer_pid'],
                                        _stat['fuzzers'], rst, ds_alive, lbl, rst, _stat['execs_done'], ds_exec, lbl, rst, slc,
                                        _stat['execs_per_sec'], ds_speed, rst, lbl, rst, _stat['pending_total'],
                                        _stat['pending_favs'], ds_pend, lbl, rst, clc, _stat['unique_crashes'], rst, ds_crash)
    else:
        pretty_stat = "[%s #%s]\nAlive: %d/%d%s\nExecs: %d%sm\nSpeed: %.1f%sx/s\n" \
                      "Pend: %d/%d%s\nCrashes: %d%s" %\
                      (_stat['afl_banner'], _stat['host'], _stat['fuzzer_pid'], _stat['fuzzers'], ds_alive,
                       _stat['execs_done'], ds_exec, _stat['execs_per_sec'], ds_speed,
                       _stat['pending_total'], _stat['pending_favs'], ds_pend, _stat['unique_crashes'], ds_crash)
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

    # { 'fuzzer_dir': (stat, old_stat) }
    stat_dict = dict()

    while not doExit:
        try:
            for fuzzer in config_fuzz_directories:
                stats = load_stats(fuzzer)

                if not stats:
                    continue

                sum_stats = summarize_stats(stats)

                try:
                    # stat_dict has already been initialized for fuzzer
                    #  old_stat <- last_stat
                    old_stats = stat_dict[fuzzer][0].copy()
                except KeyError:
                    # stat_dict has not yet been initialized for fuzzer
                    #  old_stat <- cur_stat
                    old_stats = sum_stats.copy()

                # initialize/update stat_dict
                stat_dict[fuzzer] = (sum_stats, old_stats)

                stat_change = diff_stats(sum_stats, old_stats)

                if not diff_stats:
                    continue

                print(prettify_stat(sum_stats, stat_change, True))

                tweet = prettify_stat(sum_stats, stat_change, False)

                l = len(tweet)
                c = clr.LRD if l>140 else clr.LGN
                print_ok("Tweeting status (%s%d" % (c, l) + clr.RST + " chars)...")

                try:
                    twitter_inst.statuses.update(status=shorten_tweet(tweet))
                except (twitter.TwitterHTTPError, URLError):
                    print_warn("Problem connecting to Twitter! Tweet not sent!")
                except Exception as e:
                    print_err("Sending tweet failed (Reason: " + clr.GRA + "%s" % e.__cause__ + clr.RST + ")")

            if float(config_interval) < 0:
                doExit = True
            else:
                time.sleep(float(config_interval)*60)
        except KeyboardInterrupt:
                print("\b\b")
                print_ok("Aborted by user. Good bye!")
                doExit = True


if __name__ == "__main__":
    main(sys.argv)
