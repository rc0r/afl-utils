from afl_utils import afl_multikill

import os
import subprocess
import unittest
import time


class SampleIndexTestCase(unittest.TestCase):
    def setUp(self):
        # Use to set up test environment prior to test case
        # invocation
        pass

    def tearDown(self):
        # Use for clean up after tests have run
        pass

    def setup_testprocess(self, session):
        # spawn dummy process in a new process group
        new_proc = subprocess.Popen(['setsid', 'setsid', 'python', 'testdata/dummy_process/dummyproc.py'])

        # write/append PGID to file /tmp/afl-multicore.PGID.<SESSION>
        f = open("/tmp/afl_multicore.PGID.%s" % session, "a")
        if f.writable():
            f.write("%d\n" % new_proc.pid)      # PGID ok
            f.write("%d\n" % 0x7fffffff)        # PGID invalid
        f.close()
        time.sleep(0.1)

    def test_kill_session(self):
        test_session = 'dummy_proc_01'

        # test missing PGID file
        with self.assertRaises(SystemExit) as se:
            afl_multikill.kill_session('Invalid-multikill-session')
        self.assertEqual(se.exception.code, 1)

        # test with dummy process
        self.setup_testprocess(test_session)
        self.assertIsNone(afl_multikill.kill_session(test_session))

    def test_main(self):
        test_session = 'dummy_proc_02'

        # fail test
        with self.assertRaises(SystemExit) as se:
            afl_multikill.main(['afl_multikill', '-S', 'test_session'])
        self.assertEqual(se.exception.code, 1)

        # success test with dummy process
        self.setup_testprocess(test_session)
        with self.assertRaises(SystemExit) as se:
            afl_multikill.main(['afl_multikill', '-S', test_session])
        self.assertEqual(se.exception.code, 0)
