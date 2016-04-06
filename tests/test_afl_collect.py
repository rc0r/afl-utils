from afl_utils import afl_collect
from afl_utils.SampleIndex import SampleIndex

import os
import shutil
import subprocess
import unittest


class AflCollectTestCase(unittest.TestCase):
    def setUp(self):
        # Use to set up test environment prior to test case
        # invocation
        os.makedirs('testdata/sync/fuzz000/crashes', exist_ok=True)
        os.makedirs('testdata/sync/fuzz001/crashes', exist_ok=True)
        os.makedirs('testdata/output', exist_ok=True)
        self.init_queue_dir('testdata/sync/fuzz000/queue')
        self.init_queue_dir('testdata/sync/fuzz001/queue')
        self.clean_remove('testdata/read_only')
        self.clean_remove('testdata/dbfile.db')
        self.clean_remove('testdata/gdbscript')
        subprocess.call(['make', '-C', 'testdata/crash_process'])
        if not os.path.exists('testdata/read_only_file'):
            shutil.copy('testdata/collection/dummy_sample0', 'testdata/read_only_file')
            os.chmod('testdata/read_only_file', 0o0444)

    def tearDown(self):
        # Use for clean up after tests have run
        self.clean_remove_dir('testdata/sync/fuzz000/crashes')
        self.clean_remove_dir('testdata/sync/fuzz001/crashes')
        self.clean_remove_dir('testdata/sync/fuzz000/queue')
        self.clean_remove_dir('testdata/sync/fuzz001/queue')
        self.clean_remove_dir('testdata/output')
        self.clean_remove_dir('testdata/test_collection_dir')
        self.clean_remove('testdata/read_only')
        self.clean_remove('testdata/dbfile.db')
        self.clean_remove('testdata/gdbscript')
        self.clean_remove_dir('testdata/crash_process/bin')
        os.chmod('testdata/read_only_file', 0o744)
        self.clean_remove('testdata/read_only_file')
        self.clean_remove('testdata/gdb_script')
        self.clean_remove('testdata/gdb_script.0')

    def init_crash_dir(self, fuzzer_dir):
        self.init_queue_dir(fuzzer_dir)

    def init_queue_dir(self, fuzzer_dir):
        self.clean_remove_dir(fuzzer_dir)
        shutil.copytree('testdata/queue', fuzzer_dir)

    def clean_remove(self, file):
        if os.path.exists(file):
            os.remove(file)

    def clean_remove_dir(self, dir):
        if os.path.exists(dir):
            shutil.rmtree(dir)

    def test_show_info(self):
        self.assertIsNone(afl_collect.show_info())

    def test_get_fuzzer_instances(self):
        fuzzer_inst = [
            ('fuzz000', ['crashes']),
            ('fuzz001', ['crashes'])
        ]
        self.assertListEqual(fuzzer_inst, sorted(afl_collect.get_fuzzer_instances('testdata/sync')))

        fuzzer_inst = [
            (os.path.abspath('testdata/sync/fuzz000'), ['crashes'])
        ]
        self.assertListEqual(fuzzer_inst, sorted(afl_collect.get_fuzzer_instances(('testdata/sync/fuzz000'))))

        fuzzer_inst = [
            ('fuzz000', ['queue']),
            ('fuzz001', ['queue'])
        ]
        self.assertListEqual(fuzzer_inst, sorted(afl_collect.get_fuzzer_instances('testdata/sync',
                                                                                  crash_dirs=False)))

        fuzzer_inst = [
            (os.path.abspath('testdata/sync/fuzz000'), ['queue'])
        ]
        self.assertListEqual(fuzzer_inst, sorted(afl_collect.get_fuzzer_instances(('testdata/sync/fuzz000'),
                                                                                  crash_dirs=False)))

    def test_get_crash_directories(self):
        fuzzer_inst = [
            ('fuzz000', ['crashes']),
            ('fuzz001', ['crashes'])
        ]
        sync_dir = os.path.abspath('testdata/sync')
        self.assertListEqual(fuzzer_inst, sorted(afl_collect.get_crash_directories(sync_dir, fuzzer_inst)))

    def test_get_queue_directories(self):
        fuzzer_inst = [
            ('fuzz000', ['queue']),
            ('fuzz001', ['queue'])
        ]
        sync_dir = os.path.abspath('testdata/sync')
        self.assertListEqual(fuzzer_inst, sorted(afl_collect.get_queue_directories(sync_dir, fuzzer_inst)))

    def test_get_samples_from_dir(self):
        sample_dir = 'testdata/queue'
        expected_result = (3, [
            'sample0',
            'sample1',
            'sample2'
        ])
        result = afl_collect.get_samples_from_dir(sample_dir)
        self.assertEqual(expected_result[0], result[0])
        self.assertListEqual(expected_result[1], sorted(result[1]))

        expected_result = (3, [
            os.path.join(sample_dir, 'sample0'),
            os.path.join(sample_dir, 'sample1'),
            os.path.join(sample_dir, 'sample2'),
        ])
        result = afl_collect.get_samples_from_dir(sample_dir, abs_path=True)
        self.assertEqual(expected_result[0], result[0])
        self.assertListEqual(expected_result[1], sorted(result[1]))

    def test_collect_samples(self):
        sync_dir = 'testdata/sync'
        fuzzer_inst = [
            ('fuzz000', ['queue']),
            ('fuzz001', ['queue'])
        ]
        expected_result = (6, [
            ('fuzz000', [
                ('queue', [
                    'sample0',
                    'sample1',
                    'sample2'
                    ]
                )]),
            ('fuzz001', [
                ('queue', [
                    'sample0',
                    'sample1',
                    'sample2'
                    ]
                 )])
        ])
        result = afl_collect.collect_samples(sync_dir, fuzzer_inst)
        self.assertEqual(expected_result[0], result[0])
        self.assertListEqual(expected_result[1], sorted(result[1]))

    def test_build_sample_index(self):
        sync_dir = 'testdata/sync'
        out_dir = 'testdata/out'
        fuzzer_inst = [
            ('fuzz000', ['queue']),
            ('fuzz001', ['queue'])
        ]
        expected_index = [
            {'input': os.path.abspath('testdata/sync/fuzz000/queue/sample0'), 'fuzzer': 'fuzz000',
             'output': 'fuzz000:sample0'},
            {'input': os.path.abspath('testdata/sync/fuzz000/queue/sample1'), 'fuzzer': 'fuzz000',
             'output': 'fuzz000:sample1'},
            {'input': os.path.abspath('testdata/sync/fuzz000/queue/sample2'), 'fuzzer': 'fuzz000',
             'output': 'fuzz000:sample2'},
            {'input': os.path.abspath('testdata/sync/fuzz001/queue/sample0'), 'fuzzer': 'fuzz001',
             'output': 'fuzz001:sample0'},
            {'input': os.path.abspath('testdata/sync/fuzz001/queue/sample1'), 'fuzzer': 'fuzz001',
             'output': 'fuzz001:sample1'},
            {'input': os.path.abspath('testdata/sync/fuzz001/queue/sample2'), 'fuzzer': 'fuzz001',
             'output': 'fuzz001:sample2'},
        ]
        result = afl_collect.build_sample_index(sync_dir, out_dir, fuzzer_inst)
        self.assertListEqual(expected_index, result.index)

    def test_copy_samples(self):
        out_dir = 'testdata/output'
        index = [
            {'input': os.path.abspath('testdata/sync/fuzz001/queue/sample2'), 'fuzzer': 'fuzz001',
             'output': 'fuzz001:sample2'},
        ]
        si = SampleIndex(out_dir, index)
        files_expected = [
            os.path.join(os.path.abspath(out_dir), index[0]['output'])
        ]
        self.assertListEqual(files_expected, afl_collect.copy_samples(si))

        ls_outdir = os.listdir(out_dir)
        self.assertListEqual([index[0]['output']], sorted(ls_outdir))

    def test_generate_sample_list(self):
        list_name = 'testdata/read_only'
        files_collected = [
            'dummy0',
            'dummy1',
            'dummy2'
        ]
        self.assertFalse(os.path.exists('testdata/read_only'))
        self.assertIsNone(afl_collect.generate_sample_list(list_name, files_collected))
        self.assertTrue(os.path.exists('testdata/read_only'))

        self.assertIsNone(afl_collect.generate_sample_list('/invalid', files_collected))

    def test_stdin_mode(self):
        self.assertTrue(afl_collect.stdin_mode('bla blubb stdin'))
        self.assertFalse(afl_collect.stdin_mode('bla blubb @@'))

    def test_generate_gdb_exploitable_script(self):
        script_filename = 'testdata/read_only_file'
        index = [
            {'input': os.path.abspath('testdata/sync/fuzz001/queue/sample2'), 'fuzzer': 'fuzz001',
             'output': 'fuzz001:sample2'},
        ]
        si = SampleIndex('testdata/output', index)

        self.assertIsNone(afl_collect.generate_gdb_exploitable_script(script_filename, si, 'bin/echo'))

        script_filename = 'testdata/gdb_script'
        self.assertIsNone(afl_collect.generate_gdb_exploitable_script(script_filename, si, '/bin/echo',
                                                                      intermediate=True))
        self.assertTrue(os.path.exists('testdata/gdb_script.0'))
        self.assertIsNone(afl_collect.generate_gdb_exploitable_script(script_filename, si, '/bin/echo'))
        self.assertTrue(os.path.exists('testdata/gdb_script'))

        afl_collect.gdb_exploitable_path = 'test'
        self.assertIsNone(afl_collect.generate_gdb_exploitable_script(script_filename, si, '/bin/echo'))
        self.assertTrue(os.path.exists('testdata/gdb_script'))

        afl_collect.gdb_exploitable_path = None
        self.assertIsNone(afl_collect.generate_gdb_exploitable_script(script_filename, si, '/bin/echo @@'))
        self.assertTrue(os.path.exists('testdata/gdb_script'))

    def test_execute_gdb_script(self):
        pass

    def test_main(self):
        argv = ['afl-collect', '-h']
        with self.assertRaises(SystemExit):
            self.assertIsNone(afl_collect.main(argv))

        argv = ['afl-collect', 'testdata/invalid_sync_dir', 'testdata/test_collection_dir', '--', 'testdata/invalid']
        self.assertIsNone(afl_collect.main(argv))

        argv = ['afl-collect', 'testdata/sync', 'testdata/test_collection_dir', '--', 'testdata/invalid']
        self.assertIsNone(afl_collect.main(argv))

        argv = ['afl-collect', 'testdata/sync', 'testdata/test_collection_dir', '--', '/bin/echo']
        self.assertIsNone(afl_collect.main(argv))

        self.assertFalse(os.path.exists('testdata/dbfile.db'))
        argv = ['afl-collect', '-d', 'testdata/dbfile.db', 'testdata/sync', 'testdata/test_collection_dir', '--', '/bin/echo']
        self.assertIsNone(afl_collect.main(argv))
        self.assertTrue(os.path.exists('testdata/dbfile.db'))

        self.init_crash_dir('testdata/sync/fuzz000/crashes')
        self.init_crash_dir('testdata/sync/fuzz001/crashes')
        argv = ['afl-collect', 'testdata/sync', 'testdata/test_collection_dir', '--', '/bin/echo']
        self.assertIsNone(afl_collect.main(argv))

        argv = ['afl-collect', '-r', 'testdata/sync', 'testdata/test_collection_dir', '--', '/bin/echo']
        self.assertIsNone(afl_collect.main(argv))

        argv = ['afl-collect', '-d', 'testdata/dbfile.db', '-e', 'gdbscript', '-r', '-rr', 'testdata/sync',
               'testdata/test_collection_dir', '--', 'testdata/crash_process/bin/crash']
        self.assertIsNone(afl_collect.main(argv))

        argv = ['afl-collect', '-g', 'gdbscript', '-f', 'testdata/read_only', 'testdata/sync',
                'testdata/test_collection_dir', '--', '/bin/echo']
        self.assertIsNone(afl_collect.main(argv))
