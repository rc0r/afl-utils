from afl_utils import afl_cron, afl_sync
from afl_utils.afl_cron import AflCronDaemon

import os
import shutil
import unittest

g_config_file = 'config/afl-cron.conf.sample'

class AflSyncTestCase(unittest.TestCase):
    def setUp(self):
        # Use to set up test environment prior to test case
        # invocation
        pass

    def tearDown(self):
        # Use for clean up after tests have run
        pass

    def clean_remove(self, file):
        if os.path.exists(file):
            os.remove(file)

    def clean_remove_dir(self, dir):
        if os.path.exists(dir):
            shutil.rmtree(dir)

    def test_load_config(self):
        config = {
            "interval": 60,
            "jobs": [
                {
                    "name": "afl-stats",
                    "description": "Job description here",
                    "module": "afl_utils.afl_stats",
                    "function": "main",
                    "params": "--quiet -c config/afl-stats.conf.sample"
                }
            ]
        }

        cron = AflCronDaemon(g_config_file)
        self.assertDictEqual(config, cron.config)

    def test_get_module(self):
        module_path = 'afl_utils.afl_sync'
        module = afl_sync

        cron = AflCronDaemon(g_config_file)
        self.assertEqual(module, cron.get_module(module_path))

        # error case
        with self.assertRaises(ValueError):
            cron.get_module('invalid_module.path')

    def test_get_member(self):
        module = afl_sync
        cls = afl_sync.AflBaseSync
        cls_name = 'AflBaseSync'
        fcn = afl_sync.main
        fcn_name = 'main'

        # get class
        cron = AflCronDaemon(g_config_file)
        self.assertEqual(cls, cron.get_member(module, cls_name))

        # get func
        cron = AflCronDaemon(g_config_file)
        self.assertEqual(fcn, cron.get_member(module, fcn_name))

        # error case
        with self.assertRaises(ValueError):
            cron.get_member(module, 'invalid_class')

    def test_run_job(self):
        # TODO
        pass

    def test_run(self):
        # TODO
        pass

    def test_show_info(self):
        self.assertIsNone(afl_cron.show_info())

    def test_main(self):
        with self.assertRaises(FileNotFoundError):
            self.assertIsNone(afl_cron.main(['afl-cron']))
