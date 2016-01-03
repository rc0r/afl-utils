from afl_utils import afl_vcrash

import os
# import subprocess
import unittest


class AflVCrashTestCase(unittest.TestCase):
    def setup(self):
        # Use to set up test environment prior to test case
        # invocation
        pass

    def tearDown(self):
        # Use for clean up after tests have run
        if os.path.exists('/tmp/afl_multicore.PGID.unittest_sess_01'):
            os.remove('/tmp/afl_multicore.PGID.unittest_sess_01')

        if os.path.exists('testdata/invalid'):
            os.remove('testdata/invalid')

        if os.path.exists('testdata/test_coll/invalid'):
            os.remove('testdata/test_coll/invalid')

        if os.path.exists('testdata/test_coll'):
            os.rmdir('testdata/test_coll')

        if os.path.exists('testdata/vcrash_filelist'):
            os.remove('testdata/vcrash_filelist')

    def test_show_info(self):
        self.assertIsNone(afl_vcrash.show_info())

    def test_verify_samples(self):
        # test for invalid crash detection
        num_threads = 1
        samples = ['testdata/sync/fuzz000/fuzzer_stats']    # invalid (non-crashing) sample
        target_cmd = 'ls'
        timeout_secs = 3

        self.assertEqual((['testdata/sync/fuzz000/fuzzer_stats'], []),
                         afl_vcrash.verify_samples(num_threads, samples, target_cmd, timeout_secs))

        # test for timeout detection
        num_threads = 1
        samples = ['testdata/sync/fuzz000/fuzzer_stats']    # invalid (non-crashing) sample
        target_cmd = 'python testdata/dummy_process/dummyproc.py'
        timeout_secs = 1

        self.assertEqual(([], ['testdata/sync/fuzz000/fuzzer_stats']),
                         afl_vcrash.verify_samples(num_threads, samples, target_cmd, timeout_secs))

    def test_remove_samples(self):
        # fail
        samples = ['testdata/invalid']
        with self.assertRaises(FileNotFoundError):
            afl_vcrash.remove_samples(samples, False)

        # success
        open('testdata/invalid', 'a').close()
        self.assertEqual(1, afl_vcrash.remove_samples(samples, False))

    def test_build_target_cmd(self):
        # fail
        target_cmdline = ['/some/path/to/invalid/target/binary', '--some-opt', '--some-other-opt']
        with self.assertRaises(SystemExit) as se:
            afl_vcrash.build_target_cmd(target_cmdline)
        self.assertEqual(2, se.exception.code)

        target_cmdline = ['testdata/dummy_process/dummyproc.py', '-h', '-l']
        self.assertIn('testdata/dummy_process/dummyproc.py -h -l', afl_vcrash.build_target_cmd(target_cmdline))

    def test_main(self):
        # invalid invocation
        with self.assertRaises(SystemExit) as se:
            afl_vcrash.main(['afl-vcrash', '--some-invalid-opt'])
        self.assertEqual(2, se.exception.code)

        # invalid collection dir
        with self.assertRaises(SystemExit) as se:
            afl_vcrash.main(['afl-vcrash', 'testdata/test_coll', '--', '/usr/bin/ls'])
        self.assertEqual(1, se.exception.code)

        # prepare sample collection dir
        os.mkdir('testdata/test_coll')
        open('testdata/test_coll/invalid', 'a').close()

        self.assertIsNone(afl_vcrash.main(['afl-vcrash', '-f', 'testdata/vcrash_filelist', 'testdata/test_coll',
                                           '--', '/bin/ls']))
        self.assertIs(True, os.path.exists('testdata/vcrash_filelist'))
        self.assertIs(True, os.path.exists('testdata/test_coll/invalid'))

        self.assertIsNone(afl_vcrash.main(['afl-vcrash', '-r', '-f', 'testdata/vcrash_filelist', 'testdata/test_coll',
                                           '--', '/bin/ls']))
        self.assertIs(True, os.path.exists('testdata/vcrash_filelist'))
        self.assertIs(False, os.path.exists('testdata/test_coll/invalid'))

