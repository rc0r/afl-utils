from afl_utils import afl_minimize

import os
import shutil
import subprocess
import unittest

test_sync_dir = os.path.abspath('testdata/sync')
collection_base = os.path.abspath('testdata/collection')
collection_dir = os.path.abspath('testdata/collection_test')
collection_new = os.path.abspath('testdata/collection_new')
collection_new_cmin = os.path.abspath('testdata/collection_new.cmin')
collection_new_tmin = os.path.abspath('testdata/collection_new.tmin')
collection_new_cmin_tmin = os.path.abspath('testdata/collection_new.cmin.tmin')
queue_base = os.path.abspath('testdata/queue')


class AflMinimizeTestCase(unittest.TestCase):
    def init_collection_dir(self):
        if os.path.exists(collection_dir):
            shutil.rmtree(collection_dir)
        shutil.copytree(collection_base, collection_dir)

    def setUp(self):
        # Use to set up test environment prior to test case
        # invocation
        queue_dir = os.path.join(test_sync_dir, 'fuzz000/queue')
        if os.path.exists(queue_dir):
            shutil.rmtree(queue_dir)
        shutil.copytree(queue_base, queue_dir)
        queue_dir = os.path.join(test_sync_dir, 'fuzz001/queue')
        if os.path.exists(queue_dir):
            shutil.rmtree(queue_dir)
        shutil.copytree(queue_base, queue_dir)
        self.init_collection_dir()
        subprocess.call(['make', '-C', 'testdata/crash_process'])
        os.makedirs(collection_new_cmin, exist_ok=True)
        os.makedirs(collection_new_tmin, exist_ok=True)
        os.makedirs(collection_new_cmin_tmin, exist_ok=True)

    def tearDown(self):
        # Use for clean up after tests have run
        self.del_queue_dirs(os.path.join(test_sync_dir, 'fuzz000'))
        self.del_queue_dirs(os.path.join(test_sync_dir, 'fuzz001'))

        if os.path.exists(os.path.abspath('%s.cmin' % collection_dir)):
            shutil.rmtree(os.path.abspath('%s.cmin' % collection_dir))
        if os.path.exists(os.path.abspath('%s.tmin' % collection_dir)):
            shutil.rmtree(os.path.abspath('%s.tmin' % collection_dir))
        if os.path.exists(os.path.abspath('%s.crashes' % collection_dir)):
            shutil.rmtree(os.path.abspath('%s.crashes' % collection_dir))
        if os.path.exists(os.path.abspath('%s.timeouts' % collection_dir)):
            shutil.rmtree(os.path.abspath('%s.timeouts' % collection_dir))
        if os.path.exists(os.path.abspath('testdata/crash_process/bin')):
            shutil.rmtree(os.path.abspath('testdata/crash_process/bin'))
        if os.path.exists(collection_dir):
            shutil.rmtree(collection_dir)
        if os.path.exists(collection_new):
            shutil.rmtree(collection_new)
        if os.path.exists(collection_new_cmin):
            shutil.rmtree(collection_new_cmin)
        if os.path.exists(collection_new_tmin):
            shutil.rmtree(collection_new_tmin)
        if os.path.exists(collection_new_cmin_tmin):
            shutil.rmtree(collection_new_cmin_tmin)

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
        self.init_collection_dir()
        self.assertEqual(False, afl_minimize.invoke_cmin(collection_dir, '%s.cmin' % collection_dir,
                                                         '/bin/echo', mem_limit=100, timeout=100, qemu=True))

    def test_invoke_tmin(self):
        self.init_collection_dir()
        self.assertNotEqual(0, afl_minimize.invoke_tmin(collection_dir, '%s.tmin' % collection_dir,
                                                        '/bin/echo', mem_limit=100, timeout=100, qemu=True))

    def test_invoke_dryrun(self):
        self.init_collection_dir()
        input_files = [
            '%s/dummy_sample0' % collection_dir,
            '%s/dummy_sample1' % collection_dir,
            '%s/dummy_sample2' % collection_dir
        ]
        self.assertEqual(None, afl_minimize.invoke_dryrun(input_files, '%s.crashes' % collection_dir,
                                                          '%s.timeouts' % collection_dir,
                                                          'testdata/crash_process/bin/crash', timeout=1))

    def test_afl_reseed(self):
        test_fuzzer_queues = [('fuzz000', ['queue']), ('fuzz001', ['queue'])]

        dir_ls = [
            'fuzzer_stats',
            'queue'
        ]

        pre_queue_ls = [
            '.state',
            'sample0',
            'sample1',
            'sample2',
            'sample3',
            'sample4'
        ]

        queue_ls = [
            '.state',
            'dummy_sample0',
            'dummy_sample1',
            'dummy_sample2',
            'dummy_sample3',
            'dummy_sample4'
        ]

        self.assertListEqual(dir_ls, sorted(os.listdir(os.path.join(test_sync_dir, 'fuzz000'))))
        self.assertListEqual(dir_ls, sorted(os.listdir(os.path.join(test_sync_dir, 'fuzz001'))))
        self.assertListEqual(pre_queue_ls, sorted(os.listdir(os.path.join(test_sync_dir, 'fuzz000/queue'))))
        self.assertListEqual(pre_queue_ls, sorted(os.listdir(os.path.join(test_sync_dir, 'fuzz001/queue'))))

        self.assertListEqual(test_fuzzer_queues, sorted(afl_minimize.afl_reseed('testdata/sync', collection_dir)))

        self.assertListEqual(queue_ls, sorted(os.listdir(os.path.join(test_sync_dir, 'fuzz000/queue'))))
        self.assertListEqual(queue_ls, sorted(os.listdir(os.path.join(test_sync_dir, 'fuzz001/queue'))))

    def test_main(self):
        argv = ['afl-minimize', '-h']
        with self.assertRaises(SystemExit):
            self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', collection_dir, '--', '/bin/echo']
        self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', '-c', collection_dir, 'invalid', '--', '/bin/echo']
        self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', '-c', collection_dir, 'testdata/sync', '--', '/bin/invalid_binary']
        self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', '-c', collection_dir, 'testdata/sync', '--', '/bin/echo']
        self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', '-c', collection_new, 'testdata/sync', '--', '/bin/echo']
        self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', '-c', collection_new, '--cmin', '--tmin', 'testdata/sync', '--', '/bin/echo']
        self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', '-c', collection_new, '--tmin', 'testdata/sync', '--', '/bin/echo']
        self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', '-c', collection_new, '--cmin', '--tmin', '--dry-run', 'testdata/sync', '--', '/bin/echo']
        self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', '-c', collection_new, '--cmin', '--dry-run', 'testdata/sync', '--', '/bin/echo']
        self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', '-c', collection_new, '--tmin', '--dry-run', 'testdata/sync', '--', '/bin/echo']
        self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', '-c', collection_new, '--dry-run', 'testdata/sync', '--', '/bin/echo']
        self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', '-c', collection_new, '--cmin', '--tmin', '--reseed', 'testdata/sync', '--',
                '/bin/echo']
        self.assertIsNone(afl_minimize.main(argv))

        argv = ['afl-minimize', '--dry-run', 'testdata/sync', '--', '/bin/echo']
        self.assertIsNone(afl_minimize.main(argv))
