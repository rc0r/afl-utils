from afl_utils import afl_multicore

import os
# import subprocess
import unittest

test_conf_settings = {
    'afl_margs': '-T banner',
    'dumb': 'on',
    'timeout': '200+',
    'dict': 'dict/target.dict',
    'file': '@@',
    'interactive': False,
    'target': '/usr/bin/target',
    'input': './in',
    'cmdline': '-a -b -c -d',
    'session': 'SESSION',
    'qemu': 'on',
    'output': './out',
    'dirty': 'on',
    'mem_limit': '150',
    'slave_only': False
}
test_environment = [
    ('AFL_PERSISTENT', '1')
]

test_afl_cmdline = [
    '-f', '@@', '-t', '200+', '-m', '150', '-Q', '-d', '-n', '-x', 'dict/target.dict', '-T banner', '-i',
    './in', '-o', './out'
]


class AflMulticoreTestCase(unittest.TestCase):
    def setup(self):
        # Use to set up test environment prior to test case
        # invocation
        pass

    def tearDown(self):
        # Use for clean up after tests have run
        pass

    def test_show_info(self):
        self.assertIsNone(afl_multicore.show_info())

    def test_read_config(self):
        conf_settings, environment = afl_multicore.read_config('testdata/afl-multicore.conf.test')

        self.assertDictEqual(conf_settings, test_conf_settings)
        self.assertEqual(environment, test_environment)

    def test_afl_cmdline_from_config(self):
        afl_cmdline = afl_multicore.afl_cmdline_from_config(test_conf_settings)
        self.assertEqual(afl_cmdline, test_afl_cmdline)

    # def test_setup_screen(self):
    #     if afl_multicore.check_screen():
    #         env_list = [
    #             ('test_env_var1', '1'),
    #             ('test_env_var2', '2'),
    #             ('test_env_var3', '3'),
    #             ('test_env_var4', '4'),
    #             ('test_env_var5', '5')
    #         ]
    #         afl_multicore.setup_screen(1, env_list)
    #
    #         subprocess.Popen("screen -X select 1".split())
    #
    #         for e in env_list:
    #             self.assertEqual(os.environ[e[0]], e[1])
    #
    #         subprocess.Popen("logout".split())
    #     else:
    #         print("Not in a screen session, will skip test_setup_screen_env!")

    def test_check_screen(self):
        if os.environ.get('STY'):
            sty = os.environ['STY']
            self.assertTrue(afl_multicore.check_screen())
            os.environ.pop('STY')
            self.assertFalse(afl_multicore.check_screen())
            os.environ['STY'] = sty
        else:
            self.assertFalse(afl_multicore.check_screen())
            os.environ['STY'] = 'screen'
            self.assertTrue(afl_multicore.check_screen())
            os.environ.pop('STY')
            self.assertFalse(afl_multicore.check_screen())
