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
import sys
import socket
import twitter
from urllib.error import URLError

import afl_utils
from afl_utils.AflPrettyPrint import clr, print_ok, print_warn, print_err
from db_connectors import con_sqlite


db_table_spec = """`id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, `last_update` INTEGER NOT NULL, `start_time`INTEGER NOT NULL,
`fuzzer_pid` INTEGER NOT NULL, `cycles_done` INTEGER NOT NULL, `execs_done` INTEGER NOT NULL,
`execs_per_sec` REAL NOT NULL, `paths_total` INTEGER NOT NULL, `paths_favored` INTEGER NOT NULL,
`paths_found` INTEGER NOT NULL, `paths_imported` INTEGER NOT NULL, `max_depth` INTEGER NOT NULL,
`cur_path` INTEGER NOT NULL, `pending_favs` INTEGER NOT NULL, `pending_total` INTEGER NOT NULL,
`variable_paths` INTEGER NOT NULL, `stability` REAL, `bitmap_cvg` REAL NOT NULL,
`unique_crashes` INTEGER NOT NULL, `unique_hangs` INTEGER NOT NULL, `last_path` INTEGER NOT NULL,
`last_crash` INTEGER NOT NULL, `last_hang` INTEGER NOT NULL, `execs_since_crash` INTEGER NOT NULL,
`exec_timeout` INTEGER NOT NULL, `afl_banner` VARCHAR(200) NOT NULL, `afl_version` VARCHAR(10) NOT NULL,
`command_line` VARCHAR(1000)"""


def show_info():
    print(clr.CYA + "afl-stats " + clr.BRI + "%s" % afl_utils.__version__ + clr.RST + " by %s" % afl_utils.__author__)
    print("Send stats of afl-fuzz jobs to Twitter.")
    print("")


def read_config(config_file):
    config_file = os.path.abspath(os.path.expanduser(config_file))

    if not os.path.isfile(config_file):
        print_err("Config file not found!")
        sys.exit(1)

    with open(config_file, 'r') as raw_config:
        config = json.load(raw_config)
        return config


def twitter_init(config):
    try:
        config['twitter_creds_file'] = os.path.abspath(os.path.expanduser(config['twitter_creds_file']))
        if not os.path.exists(config['twitter_creds_file']):
            twitter.oauth_dance("fuzzer_stats", config['twitter_consumer_key'],
                                config['twitter_consumer_secret'], config['twitter_creds_file'])
        oauth_token, oauth_secret = twitter.read_token_file(config['twitter_creds_file'])
        twitter_instance = twitter.Twitter(auth=twitter.OAuth(oauth_token, oauth_secret,
                                                              config['twitter_consumer_key'],
                                                              config['twitter_consumer_secret']))
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
    except (OSError, ProcessLookupError):
        return 0
    return 1


def parse_stat_file(stat_file, summary=True):
    try:
        f = open(stat_file, "r")
        lines = f.readlines()
        f.close()

        summary_stats = {
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

        complete_stats = {
            'last_update': '',
            'start_time': '',
            'fuzzer_pid': '',
            'cycles_done': '',
            'execs_done': '',
            'execs_per_sec': '',
            'paths_total': '',
            'paths_favored': '',
            'paths_found': '',
            'paths_imported': '',
            'max_depth': '',
            'cur_path': '',
            'pending_favs': '',
            'pending_total': '',
            'variable_paths': '',
            'stability': '',
            'bitmap_cvg': '',
            'unique_crashes': '',
            'unique_hangs': '',
            'last_path': '',
            'last_crash': '',
            'last_hang': '',
            'execs_since_crash': '',
            'exec_timeout': '',
            'afl_banner': '',
            'afl_version': '',
            'command_line': ''
        }
        
        for l in lines:
            if summary:
                stats = summary_stats
                for k in stats.keys():
                    if k != "fuzzer_pid":
                        if k in l:
                            stats[k] = l[19:].strip(": \r\n")
                    else:
                        if k in l:
                            stats[k] = fuzzer_alive(int(l[19:].strip(": \r\n")))
            else:
                stats = complete_stats
                for k in stats.keys():
                    if k in l:
                        stats[k] = l[19:].strip(": %\r\n")

        return stats
    except FileNotFoundError as e:
        print_warn("Stat file " + clr.GRA + "%s" % e.filename + clr.RST + " not found!")

    return None


def load_stats(fuzzer_dir, summary=True):
    fuzzer_dir = os.path.abspath(os.path.expanduser(fuzzer_dir))

    if not os.path.isdir(fuzzer_dir):
        print_warn("Invalid fuzzing directory specified: " + clr.GRA + "%s" % fuzzer_dir + clr.RST)
        return None

    fuzzer_stats = []

    if os.path.isfile(os.path.join(fuzzer_dir, "fuzzer_stats")):
        # single afl-fuzz job
        stats = parse_stat_file(os.path.join(fuzzer_dir, "fuzzer_stats"), summary)
        if stats:
            fuzzer_stats.append(stats)
    else:
        fuzzer_inst = []
        for fdir in os.listdir(fuzzer_dir):
            if os.path.isdir(os.path.join(fuzzer_dir, fdir)):
                fuzzer_inst.append(os.path.join(fuzzer_dir, fdir, "fuzzer_stats"))

        for stat_file in fuzzer_inst:
            stats = parse_stat_file(stat_file, summary)
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

    # if int(_dstat['execs_done']) == 0:
    if _dstat['execs_done'] == 0:
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

        # if int(_dstat['execs_done']) < 0:
        if _dstat['execs_done'] < 0:
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


def dump_stats(config_settings, database):
    for sync_dir in config_settings['fuzz_dirs']:
        fuzzer_stats = load_stats(sync_dir, summary=False)
        for fuzzer in fuzzer_stats:
            # create different table for every afl instance
            # table = 'fuzzer_stats_{}'.format(fuzzer['afl_banner'])
            #
            # django compatible: put everything into one table (according
            # to django plots app model)
            # Differentiate data based on afl_banner, so don't override
            # it manually! afl-multicore will create a unique banner for
            # every fuzzer!
            table = 'plots_fuzzerstats'
            database.init_database(table, db_table_spec)
            if not database.dataset_exists(table, fuzzer, ['last_update', 'afl_banner']):
                database.insert_dataset(table, fuzzer)


def fetch_stats(config_settings, twitter_inst):
    stat_dict = dict()
    for fuzzer in config_settings['fuzz_dirs']:
        stats = load_stats(fuzzer)

        if not stats:
            continue

        sum_stats = summarize_stats(stats)

        try:
            with open('.afl_stats.{}'.format(os.path.basename(fuzzer)), 'r') as f:
                old_stats = json.load(f)
        except FileNotFoundError:
            old_stats = sum_stats.copy()

        # initialize/update stat_dict
        stat_dict[fuzzer] = (sum_stats, old_stats)

        stat_change = diff_stats(sum_stats, old_stats)

        with open('.afl_stats.{}'.format(os.path.basename(fuzzer)), 'w') as f:
            json.dump(sum_stats, f)

        print(prettify_stat(sum_stats, stat_change, True))

        tweet = prettify_stat(sum_stats, stat_change, False)

        l = len(tweet)
        c = clr.LRD if l > 140 else clr.LGN

        if twitter_inst:
            print_ok("Tweeting status (%s%d" % (c, l) + clr.RST + " chars)...")
            try:
                twitter_inst.statuses.update(status=shorten_tweet(tweet))
            except (twitter.TwitterHTTPError, URLError):
                print_warn("Problem connecting to Twitter! Tweet not sent!")
            except Exception as e:
                print_err("Sending tweet failed (Reason: " + clr.GRA + "%s" % e.__cause__ + clr.RST + ")")


def main(argv):
    parser = argparse.ArgumentParser(description="Post selected contents of fuzzer_stats to Twitter.",
                                     usage="afl-stats [-h] [-c config] [-d database] [-t]\n")

    parser.add_argument("-c", "--config", dest="config_file",
                        help="afl-stats config file (Default: afl-stats.conf)!", default="afl-stats.conf")
    parser.add_argument("-d", "--database", dest="database_file",
                        help="Dump stats history into database.")
    parser.add_argument('-t', '--twitter', dest='twitter', action='store_const', const=True,
                        help='Post stats to twitter (Default: off).', default=False)
    parser.add_argument('-q', '--quiet', dest='quiet', action='store_const', const=True,
                        help='Suppress any output (Default: off).', default=False)

    args = parser.parse_args(argv[1:])

    if not args.quiet:
        show_info()

    if args.database_file:
        db_file = os.path.abspath(os.path.expanduser(args.database_file))
    else:
        db_file = None

    if db_file:
        lite_db = con_sqlite.sqliteConnector(db_file, verbose=True)
    else:
        lite_db = None

    config_settings = read_config(args.config_file)

    if lite_db:
        dump_stats(config_settings, lite_db)
        lite_db.commit_close()

    if args.twitter:
        twitter_inst = twitter_init(config_settings)
    else:
        twitter_inst = None

    fetch_stats(config_settings, twitter_inst)


if __name__ == "__main__":
    main(sys.argv)
