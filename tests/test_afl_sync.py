from afl_utils import afl_sync
from afl_utils.afl_sync import AflRsync

import os
import shutil
import unittest


class AflSyncTestCase(unittest.TestCase):
    def setUp(self):
        # Use to set up test environment prior to test case
        # invocation
        os.makedirs('testdata/rsync_tmp_store', exist_ok=True)
        os.makedirs('testdata/sync/fuzz000/crashes', exist_ok=True)
        os.makedirs('testdata/sync/fuzz000/hangs', exist_ok=True)
        os.makedirs('testdata/sync/fuzz000/.cur_input', exist_ok=True)
        os.makedirs('testdata/sync/fuzz001/.cur_input', exist_ok=True)
        os.makedirs('testdata/sync/fuzz002.sync', exist_ok=True)
        os.makedirs('testdata/sync/invalid_fuzz000', exist_ok=True)
        os.makedirs('testdata/sync/invalid_fuzz001', exist_ok=True)
        # push
        os.makedirs('testdata/rsync_output_push', exist_ok=True)
        # pull
        os.makedirs('testdata/rsync_output_pull/fuzz000.sync', exist_ok=True)
        os.makedirs('testdata/rsync_output_pull/fuzz001.sync', exist_ok=True)
        os.makedirs('testdata/rsync_output_pull/other_fuzz000.sync', exist_ok=True)
        os.makedirs('testdata/rsync_output_pull/other_fuzz000.sync/.cur_input', exist_ok=True)
        os.makedirs('testdata/rsync_output_pull/other_fuzz000.sync/crashes', exist_ok=True)
        os.makedirs('testdata/rsync_output_pull/other_fuzz001.sync', exist_ok=True)
        os.makedirs('testdata/rsync_output_pull/other_fuzz001.sync/.cur_input', exist_ok=True)
        os.makedirs('testdata/rsync_output_pull/other_invalid_fuzz000.sync', exist_ok=True)
        # sync
        os.makedirs('testdata/rsync_output_sync/other_fuzz000.sync', exist_ok=True)
        os.makedirs('testdata/rsync_output_sync/other_fuzz001.sync', exist_ok=True)
        os.makedirs('testdata/rsync_output_sync/other_invalid_fuzz000.sync', exist_ok=True)

    def tearDown(self):
        # Use for clean up after tests have run
        self.clean_remove_dir('testdata/rsync_tmp_store')
        self.clean_remove_dir('testdata/sync/fuzz000/crashes')
        self.clean_remove_dir('testdata/sync/fuzz000/hangs')
        self.clean_remove_dir('testdata/sync/fuzz000/.cur_input')
        self.clean_remove_dir('testdata/sync/fuzz001/.cur_input')
        self.clean_remove_dir('testdata/sync/fuzz002.sync')
        self.clean_remove_dir('testdata/sync/invalid_fuzz000')
        self.clean_remove_dir('testdata/sync/invalid_fuzz001')
        self.clean_remove_dir('testdata/sync/fuzz000.sync')
        self.clean_remove_dir('testdata/sync/fuzz001.sync')
        self.clean_remove_dir('testdata/sync/other_fuzz000.sync')
        self.clean_remove_dir('testdata/sync/other_fuzz001.sync')
        self.clean_remove_dir('testdata/sync/other_invalid_fuzz000.sync')
        self.clean_remove_dir('testdata/rsync_output_push')
        self.clean_remove_dir('testdata/rsync_output_pull')
        self.clean_remove_dir('testdata/rsync_output_sync')
        self.clean_remove_dir('testdata/new_sync')

    def clean_remove(self, file):
        if os.path.exists(file):
            os.remove(file)

    def clean_remove_dir(self, dir):
        if os.path.exists(dir):
            shutil.rmtree(dir)

    def test_show_info(self):
        self.assertIsNone(afl_sync.show_info())

    def test_afl_rsync_init(self):
        server_config = {
            'remote_path':  'testdata/rsync_output',
        }

        fuzzer_config = {
            'sync_dir': 'testdata/sync',
            'session': 'fuzz',
            'exclude_crashes': True,
            'exclude_hangs': True,
        }

        rsync_config = {
            'get': afl_sync._rsync_default_options[:],
            'put': afl_sync._rsync_default_options[:],
        }

        afl_rsync = AflRsync(server_config, fuzzer_config, rsync_config)

        self.assertDictEqual(server_config, afl_rsync.server_config)
        self.assertDictEqual(fuzzer_config, afl_rsync.fuzzer_config)
        self.assertDictEqual(rsync_config, afl_rsync.rsync_config)

    def test_afl_rsync_prepare_sync_command(self):
        afl_rsync = AflRsync(None, None, None)

        expected_put_cmdline = [
            'rsync',
            afl_sync._rsync_default_options[0],
            '--exclude=\"exclude\"',
            'src/',
            'dst.sync/'
        ]

        expected_get_cmdline = [
            'rsync',
             afl_sync._rsync_default_options[0],
            '--exclude=\"exclude\"',
            'dst/*',
            'src/'
        ]

        self.assertListEqual(expected_put_cmdline, afl_rsync._AflRsync__prepare_rsync_commandline('src', 'dst',
                                                                                                  list(afl_sync._rsync_default_options),
                                                                                                  rsync_excludes=[
                                                                                                      'exclude']))
        self.assertListEqual(expected_get_cmdline, afl_rsync._AflRsync__prepare_rsync_commandline('src', 'dst',
                                                                                    list(afl_sync._rsync_default_options),
                                                                                    rsync_excludes=['exclude'],
                                                                                    rsync_get=True))

    def test_afl_rsync_invoke_rsync(self):
        rsync_cmdline = ['rsync', '--help']
        afl_rsync = AflRsync(None, None, None)

        self.assertTrue(afl_rsync._AflRsync__invoke_rsync(rsync_cmdline))
        self.assertFalse(afl_rsync._AflRsync__invoke_rsync(['rsync']))

    def test_afl_rsync_get_fuzzers(self):
        fuzzer_config = {
            'sync_dir': 'testdata/sync',
            'session': 'fuzz',
            'exclude_crashes': True,
            'exclude_hangs': True,
        }

        expected_fuzzers = [
            'fuzz000',
            'fuzz001',
            'invalid_fuzz000',
            'invalid_fuzz001'
        ]

        afl_rsync = AflRsync(None, fuzzer_config, None)
        self.assertListEqual(sorted(expected_fuzzers), sorted(afl_rsync._AflRsync__get_fuzzers()))

    def test_afl_rsync_put(self):
        local_path = 'testdata/sync/fuzz000'
        remote_path = 'testdata/rsync_tmp_store/fuzz000'
        excludes = ['crashes*/', 'hangs*/']

        rsync_config = {
            'get': afl_sync._rsync_default_options[:],
            'put': afl_sync._rsync_default_options[:],
        }

        afl_rsync = AflRsync(None, None, rsync_config)
        self.assertTrue(afl_rsync.rsync_put(local_path, remote_path, afl_rsync.rsync_config['put'], rsync_excludes=excludes))
        self.assertTrue(os.path.exists(remote_path + '.sync/fuzzer_stats'))
        self.assertTrue(os.path.exists(remote_path + '.sync/.cur_input'))
        self.assertFalse(os.path.exists(remote_path + '.sync/crashes'))
        self.assertFalse(os.path.exists(remote_path + '.sync/hangs'))

    def test_afl_rsync_get(self):
        local_path = 'testdata/rsync_tmp_store/fuzz000_get'
        remote_path = 'testdata/sync/fuzz000'
        excludes = ['crashes*/', 'hangs*/']

        rsync_config = {
            'get': afl_sync._rsync_default_options[:],
            'put': afl_sync._rsync_default_options[:],
        }

        afl_rsync = AflRsync(None, None, rsync_config)
        self.assertTrue(afl_rsync.rsync_get(remote_path, local_path, afl_rsync.rsync_config['get'], rsync_excludes=excludes))
        self.assertTrue(os.path.exists(local_path + '/fuzzer_stats'))
        self.assertFalse(os.path.exists(local_path + '/crashes'))
        self.assertFalse(os.path.exists(local_path + '/hangs'))

    def test_afl_rsync_push(self):
        server_config = {
            'remote_path': 'testdata/rsync_output_push',
        }

        fuzzer_config = {
            'sync_dir': 'testdata/sync',
            'session': 'fuzz',
            'exclude_crashes': True,
            'exclude_hangs': True,
        }

        rsync_config = {
            'get': afl_sync._rsync_default_options[:],
            'put': afl_sync._rsync_default_options[:],
        }

        afl_rsync = AflRsync(server_config, fuzzer_config, rsync_config)
        self.assertIsNone(afl_rsync.push())
        self.assertTrue(os.path.exists('testdata/rsync_output_push/fuzz000.sync'))
        self.assertFalse(os.path.exists('testdata/rsync_output_push/fuzz000.sync/.cur_input'))
        self.assertTrue(os.path.exists('testdata/rsync_output_push/fuzz001.sync'))
        self.assertFalse(os.path.exists('testdata/rsync_output_push/fuzz002.sync'))
        self.assertFalse(os.path.exists('testdata/rsync_output_push/fuzz002.sync.sync'))
        self.assertFalse(os.path.exists('testdata/rsync_output_push/invalid_fuzz000.sync'))
        self.assertFalse(os.path.exists('testdata/rsync_output_push/invalid_fuzz001.sync'))

    def test_afl_rsync_pull_session(self):
        server_config = {
            'remote_path': 'testdata/rsync_output_pull',
        }

        fuzzer_config = {
            'sync_dir': 'testdata/sync',
            'session': 'other_fuzz',
            'exclude_crashes': True,
            'exclude_hangs': True,
        }

        rsync_config = {
            'get': afl_sync._rsync_default_options[:],
            'put': afl_sync._rsync_default_options[:],
        }

        afl_rsync = AflRsync(server_config, fuzzer_config, rsync_config)
        self.assertIsNone(afl_rsync.pull())
        self.assertTrue(os.path.exists('testdata/sync/other_fuzz000.sync'))
        self.assertTrue(os.path.exists('testdata/sync/other_fuzz000.sync/crashes'))
        self.assertFalse(os.path.exists('testdata/sync/other_fuzz000.sync/.cur_input'))
        self.assertTrue(os.path.exists('testdata/sync/other_fuzz001.sync'))
        self.assertFalse(os.path.exists('testdata/sync/other_fuzz001.sync/.cur_input'))
        self.assertFalse(os.path.exists('testdata/sync/other_invalid_fuzz000.sync'))
        self.assertFalse(os.path.exists('testdata/sync/fuzz000.sync'))
        self.assertFalse(os.path.exists('testdata/sync/fuzz001.sync'))

    def test_afl_rsync_pull_all(self):
        server_config = {
            'remote_path': 'testdata/rsync_output_pull',
        }

        fuzzer_config = {
            'sync_dir': 'testdata/sync',
            'session': None,
            'exclude_crashes': True,
            'exclude_hangs': True,
        }

        rsync_config = {
            'get': afl_sync._rsync_default_options[:],
            'put': afl_sync._rsync_default_options[:],
        }

        afl_rsync = AflRsync(server_config, fuzzer_config, rsync_config)
        self.assertIsNone(afl_rsync.pull())
        self.assertTrue(os.path.exists('testdata/sync/other_fuzz000.sync'))
        self.assertTrue(os.path.exists('testdata/sync/other_fuzz001.sync'))
        self.assertFalse(os.path.exists('testdata/sync/other_fuzz000.sync/.cur_input'))
        self.assertFalse(os.path.exists('testdata/sync/other_fuzz001.sync/.cur_input'))
        self.assertTrue(os.path.exists('testdata/sync/other_invalid_fuzz000.sync'))
        self.assertFalse(os.path.exists('testdata/sync/fuzz000.sync'))
        self.assertFalse(os.path.exists('testdata/sync/fuzz001.sync'))

    def test_afl_rsync_sync(self):
        server_config = {
            'remote_path': 'testdata/rsync_output_sync',
        }

        fuzzer_config = {
            'sync_dir': 'testdata/sync',
            'session': None,
            'exclude_crashes': True,
            'exclude_hangs': True,
        }

        rsync_config = {
            'get': afl_sync._rsync_default_options[:],
            'put': afl_sync._rsync_default_options[:],
        }

        afl_rsync = AflRsync(server_config, fuzzer_config, rsync_config)
        self.assertIsNone(afl_rsync.sync())

        # pull assertions
        self.assertTrue(os.path.exists('testdata/sync/other_fuzz000.sync'))
        self.assertTrue(os.path.exists('testdata/sync/other_fuzz001.sync'))
        self.assertTrue(os.path.exists('testdata/sync/other_invalid_fuzz000.sync'))
        self.assertFalse(os.path.exists('testdata/sync/fuzz000.sync'))
        self.assertFalse(os.path.exists('testdata/sync/fuzz001.sync'))

        # push assertions
        self.assertTrue(os.path.exists('testdata/rsync_output_sync/fuzz000.sync'))
        self.assertTrue(os.path.exists('testdata/rsync_output_sync/fuzz001.sync'))
        self.assertFalse(os.path.exists('testdata/rsync_output_sync/fuzz002.sync'))
        self.assertFalse(os.path.exists('testdata/rsync_output_sync/fuzz002.sync.sync'))
        self.assertTrue(os.path.exists('testdata/rsync_output_sync/invalid_fuzz000.sync'))
        self.assertTrue(os.path.exists('testdata/rsync_output_sync/invalid_fuzz001.sync'))

    def test_main(self):
        argv = [
            'afl-sync'
        ]

        with self.assertRaises(SystemExit):
            self.assertIsNone(afl_sync.main(argv))

        argv = [
            'afl-sync',
            'put',
            'src',
            'dst'
        ]
        with self.assertRaises(SystemExit) as e:
            afl_sync.main(argv)
        self.assertEqual(1, e.exception.code)

        argv = [
            'afl-sync',
            'push',
            'testdata/new_sync',
            'testdata/rsync_output_push'
        ]
        with self.assertRaises(SystemExit) as e:
            afl_sync.main(argv)
        self.assertEqual(1, e.exception.code)

        argv = [
            'afl-sync',
            'pull',
            'testdata/new_sync',
            'testdata/rsync_output_pull'
        ]
        self.assertIsNone(afl_sync.main(argv))

        argv = [
            'afl-sync',
            'push',
            'testdata/sync',
            'testdata/rsync_output_push'
        ]
        self.assertIsNone(afl_sync.main(argv))
        self.assertTrue(os.path.exists('testdata/rsync_output_push/fuzz000.sync'))
        self.assertTrue(os.path.exists('testdata/rsync_output_push/fuzz001.sync'))
        self.assertFalse(os.path.exists('testdata/rsync_output_push/fuzz002.sync'))
        self.assertFalse(os.path.exists('testdata/rsync_output_push/fuzz002.sync.sync'))
        self.assertTrue(os.path.exists('testdata/rsync_output_push/invalid_fuzz000.sync'))
        self.assertTrue(os.path.exists('testdata/rsync_output_push/invalid_fuzz001.sync'))

        argv = [
            'afl-sync',
            'pull',
            'testdata/sync',
            'testdata/rsync_output_pull'
        ]
        self.assertIsNone(afl_sync.main(argv))
        self.assertTrue(os.path.exists('testdata/sync/other_fuzz000.sync'))
        self.assertTrue(os.path.exists('testdata/sync/other_fuzz001.sync'))
        self.assertTrue(os.path.exists('testdata/sync/other_invalid_fuzz000.sync'))
        self.assertFalse(os.path.exists('testdata/sync/fuzz000.sync'))
        self.assertFalse(os.path.exists('testdata/sync/fuzz001.sync'))

        argv = [
            'afl-sync',
            'sync',
            'testdata/sync',
            'testdata/rsync_output_sync'
        ]
        self.assertIsNone(afl_sync.main(argv))
        # pull assertions
        self.assertTrue(os.path.exists('testdata/sync/other_fuzz000.sync'))
        self.assertTrue(os.path.exists('testdata/sync/other_fuzz001.sync'))
        self.assertTrue(os.path.exists('testdata/sync/other_invalid_fuzz000.sync'))
        self.assertFalse(os.path.exists('testdata/sync/fuzz000.sync'))
        self.assertFalse(os.path.exists('testdata/sync/fuzz001.sync'))

        # push assertions
        self.assertTrue(os.path.exists('testdata/rsync_output_sync/fuzz000.sync'))
        self.assertTrue(os.path.exists('testdata/rsync_output_sync/fuzz001.sync'))
        self.assertFalse(os.path.exists('testdata/rsync_output_sync/fuzz002.sync'))
        self.assertFalse(os.path.exists('testdata/rsync_output_sync/fuzz002.sync.sync'))
        self.assertTrue(os.path.exists('testdata/rsync_output_sync/invalid_fuzz000.sync'))
        self.assertTrue(os.path.exists('testdata/rsync_output_sync/invalid_fuzz001.sync'))
