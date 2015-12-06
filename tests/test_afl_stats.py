from afl_utils import afl_stats

import os
import socket
# import subprocess
import unittest

test_conf_settings = {
    'twitter_creds_file': '.afl-stats.creds',
    'interval': '30',
    'twitter_consumer_key': 'your_consumer_key_here',
    'twitter_consumer_secret': 'your_consumer_secret_here',
    'fuzz_dirs': [
        '/path/to/fuzz/dir/0',
        '/path/to/fuzz/dir/1'
    ]
}

test_stats = {
    'pending_total': '0',
    'paths_favored': '25',
    'pending_favs': '0',
    'execs_per_sec': '1546.82',
    'fuzzer_pid': 0,
    'paths_total': '420',
    'unique_crashes': '0',
    'execs_done': '372033733',
    'afl_banner': 'target_000',
    'unique_hangs': '13'
}

test_sum_stats = {
    'fuzzers': 2,
    'pending_total': 0,
    'paths_favored': 50.0,
    'pending_favs': 0,
    'execs_per_sec': 1546.82*2,
    'fuzzer_pid': 0.0,
    'paths_total': 840.0,
    'unique_crashes': 0,
    'execs_done': 372033733.0*2,
    'afl_banner': 'target_000',
    'unique_hangs': 26.0,
    'host': socket.gethostname()[:10]
}

test_diff_stats = {
    'fuzzers': 1,
    'pending_total': 0,
    'paths_favored': 25.0,
    'pending_favs': 0,
    'execs_per_sec': 1546.82,
    'fuzzer_pid': 0.0,
    'paths_total': 420.0,
    'unique_crashes': 0,
    'execs_done': 372033733.0,
    'afl_banner': 'target_000',
    'unique_hangs': 13.0,
    'host': socket.gethostname()[:10]
}


class AflStatsTestCase(unittest.TestCase):
    def setup(self):
        # Use to set up test environment prior to test case
        # invocation
        pass

    def tearDown(self):
        # Use for clean up after tests have run
        pass

    def test_show_info(self):
        self.assertIsNone(afl_stats.show_info())

    def test_read_config(self):
        conf_settings = afl_stats.read_config('testdata/afl-stats.conf.test')

        self.assertDictEqual(conf_settings, test_conf_settings)

    def test_shorten_tweet(self):
        tw_in = 'A'*140
        self.assertEqual(tw_in, afl_stats.shorten_tweet(tw_in))
        tw_in = 'ABCDEFGHIJ' * 14
        tw_in += 'xyz'
        tw_out = 'ABCDEFGHIJ' * 13
        tw_out += 'ABCDEFG...'
        self.assertEqual(tw_out, afl_stats.shorten_tweet(tw_in))

    def test_fuzzer_alive(self):
        mypid = os.getpid()
        invalidpid = -7
        self.assertEqual(1, afl_stats.fuzzer_alive(mypid))
        self.assertEqual(0, afl_stats.fuzzer_alive(invalidpid))

    def test_parse_stat_file(self):
        self.assertIsNone(afl_stats.parse_stat_file('invalid-stat-file'))
        self.assertDictEqual(test_stats, afl_stats.parse_stat_file('testdata/sync/fuzz000/fuzzer_stats'))

    def test_load_stats(self):
        self.assertIsNone(afl_stats.load_stats('invalid-fuzzer-dir'))
        fuzzer_stats = [
            test_stats,
            test_stats
        ]
        self.assertEqual([test_stats], afl_stats.load_stats('testdata/sync/fuzz000'))
        self.assertEqual(fuzzer_stats, afl_stats.load_stats('testdata/sync'))

    def test_summarize_stats(self):
        stats = [
            test_stats,
            test_stats
        ]
        self.assertDictEqual(test_sum_stats, afl_stats.summarize_stats(stats))

    def test_diff_stats(self):
        self.assertDictEqual(test_diff_stats, afl_stats.diff_stats(test_sum_stats, test_diff_stats))
        corrupt_diff_stats = test_diff_stats.copy()
        corrupt_diff_stats.pop('host')
        self.assertIsNone(afl_stats.diff_stats(test_sum_stats, corrupt_diff_stats))

    def test_prettify_stat(self):
        # ok, this is somewhat cheating...
        self.assertIsNotNone(afl_stats.prettify_stat(test_sum_stats, test_diff_stats, True))
        self.assertIsNotNone(afl_stats.prettify_stat(test_sum_stats, test_diff_stats, False))

        other_sum_stats = test_sum_stats.copy()
        other_sum_stats['fuzzer_pid'] = 1

        other_diff_stats = {
            'fuzzers': 0,
            'pending_total': 1,
            'paths_favored': 25.0,
            'pending_favs': 1,
            'execs_per_sec': 0,
            'fuzzer_pid': 0.0,
            'paths_total': 420.0,
            'unique_crashes': 1,
            'execs_done': 0,
            'afl_banner': 'target_000',
            'unique_hangs': 13.0,
            'host': socket.gethostname()[:10]
        }
        self.assertIsNotNone(afl_stats.prettify_stat(other_sum_stats, other_diff_stats))

        other_diff_stats = {
            'fuzzers': -1,
            'pending_total': 1,
            'paths_favored': 25.0,
            'pending_favs': 1,
            'execs_per_sec': -1,
            'fuzzer_pid': 0.0,
            'paths_total': 420.0,
            'unique_crashes': -1,
            'execs_done': -10,
            'afl_banner': 'target_000',
            'unique_hangs': 13.0,
            'host': socket.gethostname()[:10]
        }
        self.assertIsNotNone(afl_stats.prettify_stat(test_sum_stats, other_diff_stats))
