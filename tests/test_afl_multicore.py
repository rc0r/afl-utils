import unittest
import os
from afl_utils import afl_multicore


class AflMulticoreTestCase(unittest.TestCase):
    def setup(self):
        # Use to set up test environment prior to test case
        # invocation
        pass

    def tearDown(self):
        # Use for clean up after tests have run
        pass

    def test_check_screen(self):
        self.assertFalse(afl_multicore.check_screen())
        os.environ['STY'] = 'screen'
        self.assertTrue(afl_multicore.check_screen())
        os.environ.pop('STY')
        self.assertFalse(afl_multicore.check_screen())
