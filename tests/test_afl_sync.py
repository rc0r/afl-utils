from afl_utils import afl_sync
from afl_utils.afl_sync import AflRsync

import os
import shutil
import subprocess
import unittest


class AflSyncTestCase(unittest.TestCase):
    def setUp(self):
        # Use to set up test environment prior to test case
        # invocation
        os.makedirs('testdata/rsync_tmp_store', exist_ok=True)
        os.makedirs('testdata/sync/fuzz000/crashes', exist_ok=True)
        os.makedirs('testdata/sync/fuzz000/hangs', exist_ok=True)

    def tearDown(self):
        # Use for clean up after tests have run
        self.clean_remove_dir('testdata/rsync_tmp_store')
        self.clean_remove_dir('testdata/sync/fuzz000/crashes')
        self.clean_remove_dir('testdata/sync/fuzz000/hangs')

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
            'exclude_crashes': True,
            'exclude_hangs': True,
        }

        afl_rsync = AflRsync(server_config, fuzzer_config)

        self.assertDictEqual(server_config, afl_rsync.server_config)
        self.assertDictEqual(fuzzer_config, afl_rsync.fuzzer_config)

    def test_afl_rsync_prepare_sync_command(self):
        afl_rsync = AflRsync(None, None)

        expected_put_cmdline = [
            'rsync',
            '-ra',
            '--exclude=\"exclude\"',
            'src/',
            'dst.sync/'
        ]

        expected_get_cmdline = [
            'rsync',
            '-ra',
            '--exclude=\"exclude\"',
            'dst/',
            'src/'
        ]

        self.assertListEqual(expected_put_cmdline, afl_rsync._AflRsync__prepare_rsync_commandline('src', 'dst',
                                                                                                  rsync_excludes=[
                                                                                                      'exclude']))
        self.assertListEqual(expected_get_cmdline, afl_rsync._AflRsync__prepare_rsync_commandline('src', 'dst',
                                                                                    rsync_excludes=['exclude'],
                                                                                    rsync_get=True))

    def test_afl_rsync_invoke_rsync(self):
        rsync_cmdline = ['rsync', '--help']
        afl_rsync = AflRsync(None, None)

        self.assertTrue(afl_rsync._AflRsync__invoke_rsync(rsync_cmdline))
        self.assertFalse(afl_rsync._AflRsync__invoke_rsync(['rsync']))

    def test_afl_rsync_put(self):
        local_path = 'testdata/sync/fuzz000'
        remote_path = 'testdata/rsync_tmp_store/fuzz000'
        excludes = ['crashes*/', 'hangs*/']

        afl_rsync = AflRsync(None, None)
        self.assertTrue(afl_rsync.rsync_put(local_path, remote_path, rsync_excludes=excludes))
        self.assertTrue(os.path.exists(remote_path + '.sync/fuzzer_stats'))
        self.assertFalse(os.path.exists(remote_path + '.sync/crashes'))
        self.assertFalse(os.path.exists(remote_path + '.sync/hangs'))

    def test_afl_rsync_get(self):
        local_path = 'testdata/rsync_tmp_store/fuzz000_get'
        remote_path = 'testdata/sync/fuzz000'
        excludes = ['crashes*/', 'hangs*/']

        afl_rsync = AflRsync(None, None)
        self.assertTrue(afl_rsync.rsync_get(local_path, remote_path, rsync_excludes=excludes))
        self.assertTrue(os.path.exists(local_path + '/fuzzer_stats'))
        self.assertFalse(os.path.exists(local_path + '/crashes'))
        self.assertFalse(os.path.exists(local_path + '/hangs'))

    def test_afl_rsync_sync(self):
        afl_rsync = AflRsync(None, None)
        self.assertIsNone(afl_rsync.sync())

    def test_main(self):
        argv = [
            'afl-sync'
        ]

        self.assertIsNone(afl_sync.main(argv))
