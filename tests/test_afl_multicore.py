from afl_utils import afl_multicore

try:
    import simplejson as json
except ImportError:
    import json
import shutil
import os
import unittest

test_conf_settings = {
    'afl_margs': '-T banner',
    'fuzzer': 'afl-fuzz',
    'dumb': True,
    'timeout': '200+',
    'dict': 'dict/target.dict',
    'file': '@@',
    'interactive': True,
    'target': '/usr/bin/target',
    'input': './in',
    'cmdline': '-a -b -c -d',
    'session': 'SESSION',
    'qemu': True,
    'output': './out',
    'dirty': True,
    'mem_limit': '150',
    'master_instances': 2,
    'environment': [
        'AFL_PERSISTENT=1'
    ]
}

test_conf_settings1 = {
    'interactive': False,
    'fuzzer': 'afl-fuzz',
    'target': '/usr/bin/target',
    'input': './in',
    'cmdline': '-a -b -c -d',
    'session': 'SESSION',
    'output': './out',
    'master_instances': 0,
    'environment': [
        'AFL_PERSISTENT=1'
    ]
}

test_conf_settings2 = {
    'fuzzer': 'afl-fuzz',
    'target': '/usr/bin/target',
    'input': './in',
    'cmdline': '-a -b -c -d',
    'output': './out',
    'session': 'SESSION'
}

test_conf_settings3 = {
    'fuzzer': 'afl-fuzz',
    'afl_margs': '-T banner',
    'dumb': True,
    'timeout': '200+',
    'dict': 'dict/target.dict',
    'file': 'sample_file',
    'interactive': True,
    'target': '/usr/bin/target',
    'input': './in',
    'cmdline': '-a -b -c -d',
    'session': 'SESSION',
    'qemu': True,
    'output': './out',
    'dirty': 'on',
    'mem_limit': '150'
}

test_afl_cmdline = [
    os.path.abspath(os.path.expanduser('~/.local/bin/afl-fuzz')), '-f', '@@', '-t', '200+', '-m', '150', '-Q', '-d', '-n', '-x', 'dict/target.dict', '-T banner', '-i',
    './in', '-o', './out'
]

test_afl_cmdline2 = [
    os.path.abspath(os.path.expanduser('~/.local/bin/afl-fuzz')), '-i', './in', '-o', './out'
]

test_afl_cmdline21 = [
   os.path.abspath(os.path.expanduser('~/.local/bin/afl-fuzz')), '-i', './in', '-o', './out'
]

test_afl_cmdline3 = [
    os.path.abspath(os.path.expanduser('~/.local/bin/afl-fuzz')), '-f', 'sample_file_027', '-t', '200+', '-m', '150', '-Q', '-d', '-n', '-x', 'dict/target.dict',
    '-T banner', '-i', './in', '-o', './out'
]


class AflMulticoreTestCase(unittest.TestCase):
    def setUp(self):
        # Use to set up test environment prior to test case
        # invocation

        os.makedirs('testdata/auto_delay_sync', exist_ok=True)
        os.makedirs('testdata/auto_delay_sync/fuzz000', exist_ok=True)
        os.makedirs('testdata/auto_delay_sync/fuzz000/queue', exist_ok=True)
        os.makedirs('testdata/auto_delay_sync/fuzz000/queue/sample0', exist_ok=True)
        os.makedirs('testdata/auto_delay_sync/fuzz000/queue/sample1', exist_ok=True)
        os.makedirs('testdata/auto_delay_sync/fuzz000/queue/sample2', exist_ok=True)

    def tearDown(self):
        # Use for clean up after tests have run
        self.clean_remove('/tmp/afl_multicore.PGID.unittest_sess_01')
        self.clean_remove_dir('testdata/auto_delay_sync')

    def clean_remove(self, file):
        if os.path.exists(file):
            os.remove(file)

    def clean_remove_dir(self, dir):
        if os.path.exists(dir):
            shutil.rmtree(dir)

    @unittest.skipUnless(shutil.which('afl-fuzz') == os.path.abspath(os.path.expanduser('~/.local/bin/afl-fuzz')),
                         'afl-fuzz binary not found in expected location.')
    def test_find_fuzzer_binary(self):
        self.assertEqual(afl_multicore.find_fuzzer_binary('afl-fuzz'),
                         os.path.abspath(os.path.expanduser('~/.local/bin/afl-fuzz')))
        with self.assertRaises(SystemExit) as se:
            afl_path = afl_multicore.find_fuzzer_binary('does-not-exist')
            self.assertIsNone(afl_path)
        self.assertEqual(se.exception.code, 1)

    def test_show_info(self):
        self.assertIsNone(afl_multicore.show_info())

    def test_read_config(self):
        conf_settings = afl_multicore.read_config('testdata/afl-multicore.conf.test')
        self.assertDictEqual(test_conf_settings, conf_settings)

        conf_settings = afl_multicore.read_config('testdata/afl-multicore.conf1.test')
        self.assertDictEqual(test_conf_settings1, conf_settings)

        conf_settings = afl_multicore.read_config('testdata/afl-multicore.conf2.test')
        self.assertDictEqual(test_conf_settings2, conf_settings)

        # Config file not found
        with self.assertRaises(SystemExit) as se:
            afl_multicore.read_config('invalid-config-file')
        self.assertEqual(se.exception.code, 1)

        # JSON decode error
        with self.assertRaises(json.decoder.JSONDecodeError):
            afl_multicore.read_config('testdata/afl-multicore.conf.invalid00.test')

    @unittest.skipUnless(shutil.which('afl-fuzz') == os.path.abspath(os.path.expanduser('~/.local/bin/afl-fuzz')),
                         'afl-fuzz binary not found in expected location.')
    def test_afl_cmdline_from_config(self):
        afl_cmdline = afl_multicore.afl_cmdline_from_config(test_conf_settings, 12)
        self.assertEqual(afl_cmdline, test_afl_cmdline)

        afl_cmdline = afl_multicore.afl_cmdline_from_config(test_conf_settings2, 1)
        self.assertEqual(afl_cmdline, test_afl_cmdline2)

        afl_cmdline = afl_multicore.afl_cmdline_from_config(test_conf_settings2, 4)
        self.assertEqual(afl_cmdline, test_afl_cmdline21)

        afl_cmdline = afl_multicore.afl_cmdline_from_config(test_conf_settings3, 27)
        self.assertEqual(afl_cmdline, test_afl_cmdline3)

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

    def test_setup_screen_env(self):
        # Skip test for screen environment variable setting for now
        pass

    def test_setup_screen(self):
        # Skip test for screen window setup for now
        pass
    #     if afl_multicore.check_screen():
    #         env_list = [
    #             'test_env_var1=1',
    #             'test_env_var2=2',
    #             'test_env_var3=3',
    #             'test_env_var4=4',
    #             'test_env_var5=5'
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

    def test_sigint_handler(self):
        with self.assertRaises(SystemExit) as se:
            afl_multicore.sigint_handler(0, 0)
        self.assertEqual(se.exception.code, 0)

    def test_build_target_cmd(self):
        # invalid test
        conf_settings = {
            'target': 'testdata/dummy_process/invalid_process',
            'cmdline': ''
        }
        with self.assertRaises(SystemExit) as se:
            afl_multicore.build_target_cmd(conf_settings)
        self.assertEqual(1, se.exception.code)

        # valid test
        conf_settings = {
            'target': '/bin/sh',
            'cmdline': '--some-opt'
        }
        self.assertEqual('/bin/sh --some-opt', afl_multicore.build_target_cmd(conf_settings))

    @unittest.skipUnless(shutil.which('afl-fuzz') == os.path.abspath(os.path.expanduser('~/.local/bin/afl-fuzz')),
                         'afl-fuzz binary not found in expected location.')
    def test_build_master_cmd(self):
        conf_settings = {
            'fuzzer': 'afl-fuzz',
            'session': 'SESSION',
            'file': 'cur_input'
        }
        target_cmd = 'testdata/dummy_process/invalid_proc --some-opt %%'
        expected_master_cmd = os.path.abspath(os.path.expanduser('~/.local/bin/afl-fuzz')) + ' -f cur_input_000 -M SESSION000 -- ' + target_cmd.replace('%%', conf_settings['file']+'_000')
        master_cmd = afl_multicore.build_master_cmd(conf_settings, 0, target_cmd)

        self.assertEqual(expected_master_cmd, master_cmd)

        conf_settings = {
            'fuzzer': 'afl-fuzz',
            'session': 'SESSION',
            'file': 'cur_input',
            'master_instances': 3
        }
        target_cmd = 'testdata/dummy_process/invalid_proc --some-opt %%'
        expected_master_cmd = os.path.abspath(
            os.path.expanduser('~/.local/bin/afl-fuzz')) + ' -f cur_input_001 -M SESSION001:2/3 -- ' + target_cmd.replace(
            '%%', conf_settings['file'] + '_001')
        master_cmd = afl_multicore.build_master_cmd(conf_settings, 1, target_cmd)

        self.assertEqual(expected_master_cmd, master_cmd)

    @unittest.skipUnless(shutil.which('afl-fuzz') == os.path.abspath(os.path.expanduser('~/.local/bin/afl-fuzz')),
                         'afl-fuzz binary not found in expected location.')
    def test_build_slave_cmd(self):
        conf_settings = {
            'fuzzer': 'afl-fuzz',
            'session': 'SESSION',
            'file': 'cur_input'
        }
        target_cmd = 'testdata/dummy_process/invalid_proc --some-opt %%'
        slave_num = 3
        slave_cmd = os.path.abspath(os.path.expanduser('~/.local/bin/afl-fuzz')) + ' -f cur_input_003 -S SESSION003 -- ' + target_cmd.replace("%%", conf_settings['file']+'_003')

        self.assertEqual(slave_cmd, afl_multicore.build_slave_cmd(conf_settings, slave_num, target_cmd))

    def test_write_pgid_file(self):
        # negative test
        conf_settings = {
            'session': 'unittest_sess_01',
            'output': 'testdata/output',
            'interactive': True
        }
        self.assertIsNone(afl_multicore.write_pgid_file(conf_settings))
        self.assertIsNot(True, os.path.exists('/tmp/afl_multicore.PGID.unittest_sess_01'))

        # positive test
        conf_settings = {
            'session': 'unittest_sess_01',
            'output': 'testdata/output',
            'interactive': False
        }
        self.assertIsNone(afl_multicore.write_pgid_file(conf_settings))
        self.assertIs(True, os.path.exists('/tmp/afl_multicore.PGID.unittest_sess_01'))
        os.remove('/tmp/afl_multicore.PGID.unittest_sess_01')

        # positive test, again with implicit non-interactive mode (test for #34)
        conf_settings = {
            'session': 'unittest_sess_01',
            'output': 'testdata/output'
        }
        self.assertIsNone(afl_multicore.write_pgid_file(conf_settings))
        self.assertIs(True, os.path.exists('/tmp/afl_multicore.PGID.unittest_sess_01'))
        os.remove('/tmp/afl_multicore.PGID.unittest_sess_01')

    def test_get_started_instances(self):
        # negative test
        conf_settings = {
        }
        command = 'start'
        self.assertEqual(0, afl_multicore.get_started_instance_count(command, conf_settings))

        # positive test
        conf_settings = {
            'session': 'fuzz',
            'output': 'testdata/sync',
            'master_instances': 1,
        }
        command = 'add'
        self.assertEqual(2, afl_multicore.get_started_instance_count(command, conf_settings))

    def test_get_job_counts(self):
        jobs_arg = "23"
        expected = (23, 0)
        self.assertEqual(afl_multicore.get_job_counts(jobs_arg), expected)

        jobs_arg = "23,0"
        expected = (23, 0)
        self.assertEqual(afl_multicore.get_job_counts(jobs_arg), expected)

        jobs_arg = "12,5"
        expected = (12, 5)
        self.assertEqual(afl_multicore.get_job_counts(jobs_arg), expected)

    def test_has_master(self):
        # positive test
        conf_settings = {
        }
        self.assertTrue(afl_multicore.has_master(conf_settings, 0))

        conf_settings = {
            'session': 'fuzz',
            'output': 'testdata/sync',
            'master_instances': 1,
        }
        self.assertTrue(afl_multicore.has_master(conf_settings, 0))

        conf_settings = {
            'session': 'fuzz',
            'output': 'testdata/sync',
            'master_instances': 12,
        }
        self.assertTrue(afl_multicore.has_master(conf_settings, 11))

        # negative test
        self.assertFalse(afl_multicore.has_master(conf_settings, 12))

        conf_settings = {
            'session': 'fuzz',
            'output': 'testdata/sync',
            'master_instances': 0,
        }
        self.assertFalse(afl_multicore.has_master(conf_settings, 0))
        self.assertFalse(afl_multicore.has_master(conf_settings, 2))

        conf_settings = {
            'session': 'fuzz',
            'output': 'testdata/sync',
            'master_instances': -23,
        }
        self.assertFalse(afl_multicore.has_master(conf_settings, 0))

    def test_main(self):
        # we're only going to test some error cases
        # invalid invocation (Argparser failure)
        with self.assertRaises(SystemExit) as se:
            afl_multicore.main(['afl-multicore', '-c', 'invalid.conf', '--invalid-opt'])
        self.assertEqual(2, se.exception.code)

        # test run
        with self.assertRaises(SystemExit) as se:
            afl_multicore.main(['afl-multicore', '-c', 'testdata/afl-multicore.conf.test', '-t', 'start', '4'])
        self.assertEqual(1, se.exception.code)

        # resume run
        with self.assertRaises(SystemExit) as se:
            afl_multicore.main(['afl-multicore', '-c', 'testdata/afl-multicore.conf.test', 'resume', '4'])
        self.assertEqual(1, se.exception.code)

    def test_startup_delay(self):
        conf_settings = {
            'input': './testdata/queue',
            'output': './testdata/auto_delay_sync',
            'session': 'fuzz',
            'timeout': '2000+'
        }
        self.assertEqual(afl_multicore.startup_delay(conf_settings, 0, 'start', '3'), 3)
        self.assertAlmostEqual(afl_multicore.startup_delay(conf_settings, 0, 'start', 'auto'), 2 * 2.449489743)
        self.assertAlmostEqual(afl_multicore.startup_delay(conf_settings, 0, 'resume', 'auto'), 2 * 1.732050808)

    def test_auto_startup_delay(self):
        conf_settings = {
            'input': './testdata/queue',
            'output': './testdata/auto_delay_sync',
            'session': 'fuzz'
        }
        self.assertAlmostEqual(afl_multicore.auto_startup_delay(conf_settings, 0), 1.732050808)
        self.assertAlmostEqual(afl_multicore.auto_startup_delay(conf_settings, 37, resume=False), 2.449489743)

        conf_settings = {
            'input': './testdata/queue',
            'output': './testdata/auto_delay_sync',
            'session': 'fuzz',
            'timeout': '2000+'
        }
        self.assertAlmostEqual(afl_multicore.auto_startup_delay(conf_settings, 0), 2*1.732050808)
        self.assertAlmostEqual(afl_multicore.auto_startup_delay(conf_settings, 37, resume=False), 2*2.449489743)
