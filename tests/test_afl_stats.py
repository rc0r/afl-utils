from afl_utils import afl_stats

import os
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
