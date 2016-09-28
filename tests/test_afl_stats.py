from afl_utils import afl_stats

try:
    import simplejson as json
except ImportError:
    import json
import os
import socket
import unittest
from db_connectors import con_sqlite

test_conf_settings = {
    'twitter_creds_file': '.afl-stats.creds',
    'twitter_consumer_key': 'your_consumer_key_here',
    'twitter_consumer_secret': 'your_consumer_secret_here',
    'fuzz_dirs': [
        '/path/to/fuzz/dir/0',
        '/path/to/fuzz/dir/1',
        'testdata/sync'
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

test_complete_stats = {
    'pending_total': '0',
    'paths_favored': '25',
    'pending_favs': '0',
    'execs_per_sec': '1546.82',
    'fuzzer_pid': '9999999',
    'paths_total': '420',
    'unique_crashes': '0',
    'execs_done': '372033733',
    'afl_banner': 'target_000',
    'unique_hangs': '13',
	'start_time': '1475080845',
	'last_update': '1475081950',
	'cycles_done': '0',
	'paths_found': '0',
	'paths_imported': '83',
	'max_depth': '39',
	'cur_path': '650',
	'variable_paths': '0',
	'stability': '100.00',
	'bitmap_cvg': '18.37',
	'last_path': '1475081940',
	'last_crash': '0',
	'last_hang': '0',
	'execs_since_crash': '63393',
	'exec_timeout': '800',
	'afl_version': '2.35b'
}

test_sum_stats = {
    'fuzzers': 2,
    'pending_total': 0,
    'paths_favored': 50.0,
    'pending_favs': 0,
    'execs_per_sec': 1546.82*2,
    'fuzzer_pid': 0,
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
    'fuzzer_pid': 0,
    'paths_total': 420.0,
    'unique_crashes': 0,
    'execs_done': 372033733.0,
    'afl_banner': 'target_000',
    'unique_hangs': 13.0,
    'host': socket.gethostname()[:10]
}


class AflStatsTestCase(unittest.TestCase):
    def setUp(self):
        # Use to set up test environment prior to test case
        # invocation
        pass

    def tearDown(self):
        # Use for clean up after tests have run
        self.clean_remove('./testdata/afl-stats.db')
        self.clean_remove('./testdata/afl-stats2.db')
        try:
            os.remove('.afl_stats.sync')
        except FileNotFoundError:
            pass

    def clean_remove(self, file):
        if os.path.exists(file):
            os.remove(file)

    def test_show_info(self):
        self.assertIsNone(afl_stats.show_info())

    def test_read_config(self):
        conf_settings = afl_stats.read_config('testdata/afl-stats.conf.test')

        self.assertDictEqual(conf_settings, test_conf_settings)

        with self.assertRaises(SystemExit):
            afl_stats.read_config('/config-file-not-found')
        with self.assertRaises(json.decoder.JSONDecodeError):
            afl_stats.read_config('testdata/afl-stats.conf.invalid02.test')

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
        self.assertDictEqual(test_complete_stats, afl_stats.parse_stat_file('testdata/sync/fuzz000/fuzzer_stats', summary=False))

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

    def test_dump_stats(self):
        config_settings = {'fuzz_dirs': ['./testdata/sync/']}
        lite_db = con_sqlite.sqliteConnector('./testdata/afl-stats.db', verbose=True)
        self.assertIsNone(afl_stats.dump_stats(config_settings, lite_db))
        self.assertTrue(os.path.exists('./testdata/afl-stats.db'))

    def test_fetch_stats(self):
        config_settings = afl_stats.read_config('testdata/afl-stats.conf.test')
        twitter_inst = None

        self.assertIsNone(afl_stats.fetch_stats(config_settings, twitter_inst))
        #os.remove('.afl_stats.sync')
        self.assertIsNone(afl_stats.fetch_stats(config_settings, twitter_inst))

    def test_main(self):
        with self.assertRaises(SystemExit) as se:
            afl_stats.main(['afl-stats', '--twitter', '--config', './testdata/afl-stats.conf.test'])
        self.assertEqual(se.exception.code, 1)


    def test_main_no_twitter(self):
        afl_stats.main(['afl-stats', '--config', './testdata/afl-stats.conf.test2', '--database', 'testdata/afl-stats2.db'])
        self.assertTrue(os.path.exists('testdata/afl-stats2.db'))
