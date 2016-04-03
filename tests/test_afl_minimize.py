from afl_utils import afl_minimize

import os
import shutil
import unittest

test_sync_dir = os.path.abspath('testdata/sync')


class AflMinimizeTestCase(unittest.TestCase):
    def setUp(self):
        # Use to set up test environment prior to test case
        # invocation
        os.makedirs(os.path.join(test_sync_dir, 'fuzz000/queue'), exist_ok=True)
        os.makedirs(os.path.join(test_sync_dir, 'fuzz001/queue'), exist_ok=True)

    def tearDown(self):
        # Use for clean up after tests have run
        self.del_queue_dirs(os.path.join(test_sync_dir, 'fuzz000'))
        self.del_queue_dirs(os.path.join(test_sync_dir, 'fuzz001'))

        if os.path.exists(os.path.abspath('testdata/collection.cmin')):
            shutil.rmtree(os.path.abspath('testdata/collection.cmin'))
        if os.path.exists(os.path.abspath('testdata/collection.tmin')):
            shutil.rmtree(os.path.abspath('testdata/collection.tmin'))
        if os.path.exists(os.path.abspath('testdata/collection.crashes')):
            shutil.rmtree(os.path.abspath('testdata/collection.crashes'))
        if os.path.exists(os.path.abspath('testdata/collection.timeouts')):
            shutil.rmtree(os.path.abspath('testdata/collection.timeouts'))

    def del_queue_dirs(self, base_dir):
        ls = os.listdir(base_dir)

        queue_dirs = [q for q in ls if 'queue' in q]

        for qdir in queue_dirs:
            try:
                os.rmdir(os.path.join(base_dir, qdir))
            except OSError:
                shutil.rmtree(os.path.join(base_dir, qdir))

    def test_show_info(self):
        self.assertIsNone(afl_minimize.show_info())

    def test_invoke_cmin(self):
        self.assertEqual(False, afl_minimize.invoke_cmin('testdata/collection', 'testdata/collection.cmin',
                                                         '/bin/echo', mem_limit=100, timeout=100))

    def test_invoke_tmin(self):
        self.assertEqual(19, afl_minimize.invoke_tmin('testdata/collection', 'testdata/collection.tmin',
                                                      '/bin/echo', mem_limit=100, timeout=100))

    def test_invoke_dryrun(self):
        input_files = [
            'testdata/collection/dummy_sample0',
            'testdata/collection/dummy_sample1',
            'testdata/collection/dummy_sample2'
        ]
        self.assertEqual(None, afl_minimize.invoke_dryrun(input_files, 'testdata/collection.crashes',
                                                          'testdata/collection.timeouts', '/bin/echo'))

    def test_afl_reseed(self):
        test_fuzzer_queues = [('fuzz001', ['queue']), ('fuzz000', ['queue'])]

        dir_ls = [
            'fuzzer_stats',
            'queue'
        ]

        queue_ls = [
            'dummy_sample0',
            'dummy_sample1',
            'dummy_sample2'
        ]

        self.assertListEqual(dir_ls, os.listdir(os.path.join(test_sync_dir, 'fuzz000')))
        self.assertListEqual(dir_ls, os.listdir(os.path.join(test_sync_dir, 'fuzz001')))
        self.assertListEqual([], os.listdir(os.path.join(test_sync_dir, 'fuzz000/queue')))
        self.assertListEqual([], os.listdir(os.path.join(test_sync_dir, 'fuzz001/queue')))

        self.assertListEqual(test_fuzzer_queues, afl_minimize.afl_reseed('testdata/sync', 'testdata/collection'))

        self.assertListEqual(queue_ls, sorted(os.listdir(os.path.join(test_sync_dir, 'fuzz000/queue'))))
        self.assertListEqual(queue_ls, sorted(os.listdir(os.path.join(test_sync_dir, 'fuzz001/queue'))))
