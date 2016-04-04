from afl_utils import SampleIndex

import os
import unittest


class SampleIndexTestCase(unittest.TestCase):
    def setUp(self):
        # Use to set up test environment prior to test case
        # invocation
        pass

    def tearDown(self):
        # Use for clean up after tests have run
        pass

    def prepare_SampleIndex(self):
        test_dir = 'test_data'
        test_index = [
            {'input': 1, 'fuzzer': 'fuzz01', 'output': 'fuzz01:file01'},
            {'input': 4, 'fuzzer': 'fuzz02', 'output': 'fuzz02:file02'},
            {'input': 7, 'fuzzer': 'fuzz03', 'output': 'fuzz03:file03'},
        ]

        test_inputs = [1, 4, 7]
        test_fuzzers = ['fuzz01', 'fuzz02', 'fuzz03']
        test_outputs = ['fuzz01:file01', 'fuzz02:file02', 'fuzz03:file03']

        si = SampleIndex.SampleIndex(test_dir, test_index)

        return si, test_inputs, test_fuzzers, test_outputs

    def test_init(self):
        test_dir = 'testdata'
        test_index = []
        si = SampleIndex.SampleIndex(test_dir)

        self.assertEqual(False, si.min_filename)
        self.assertEqual(os.path.abspath(test_dir), si.output_dir)
        self.assertEqual(test_index, si.index)

        test_dir = 'afl_utils'
        test_index = ['fuzz00', 'fuzz01', 'fuzz02']
        si = SampleIndex.SampleIndex(test_dir, test_index, True)

        self.assertEqual(True, si.min_filename)
        self.assertEqual(os.path.abspath(test_dir), si.output_dir)
        self.assertEqual(test_index, si.index)

    def test_generate_output(self):
        test_dir = 'testdata'
        si = SampleIndex.SampleIndex(test_dir, min_filename=False)

        self.assertEqual('fuzzer:filename', si.__generate_output__('fuzzer', '/path/to/filename'))
        self.assertEqual('fuzzer:filename', si.__generate_output__('fuzzer', './filename'))
        self.assertEqual('fuzzer:filename', si.__generate_output__('fuzzer', '~/filename'))
        self.assertEqual('fuzzer:filename', si.__generate_output__('fuzzer', 'filename'))
        self.assertEqual('fuzzer:filename', si.__generate_output__('/bla/fuzzer', 'filename'))

        si = SampleIndex.SampleIndex(test_dir, min_filename=True)

        self.assertEqual('fuzzer:filename', si.__generate_output__('fuzzer', '/path/to/id:filename,other_info'))
        self.assertEqual('fuzzer:filename', si.__generate_output__('fuzzer', './id:filename,other_info'))
        self.assertEqual('fuzzer:filename', si.__generate_output__('fuzzer', '~/id:filename,other_info'))
        self.assertEqual('fuzzer:filename', si.__generate_output__('fuzzer', 'id:filename,other_info'))
        self.assertEqual('fuzzer:filename', si.__generate_output__('fuzzer', 'filename'))

        si = SampleIndex.SampleIndex(test_dir, omit_fuzzer_name=True)

        self.assertEqual('filename', si.__generate_output__('fuzzer', '/path/to/filename'))
        self.assertEqual('filename', si.__generate_output__('fuzzer', './filename'))
        self.assertEqual('filename', si.__generate_output__('fuzzer', '~/filename'))
        self.assertEqual('filename', si.__generate_output__('fuzzer', 'filename'))
        self.assertEqual('filename', si.__generate_output__('/bla/fuzzer', 'filename'))

    def test_remove(self):
        test_index_removed = [
            {'input': 1, 'fuzzer': 'fuzz01', 'output': 'fuzz01:file01'},
            {'input': 7, 'fuzzer': 'fuzz03', 'output': 'fuzz03:file03'},
        ]
        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()
        si.__remove__('input', [test_inputs[1]])
        self.assertEqual(test_index_removed, si.index)

        test_index_removed = [
            {'input': 7, 'fuzzer': 'fuzz03', 'output': 'fuzz03:file03'},
        ]
        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()
        si.__remove__('fuzzer', [test_fuzzers[0], test_fuzzers[1]])
        self.assertEqual(test_index_removed, si.index)

        test_index_removed = []
        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()
        si.__remove__('output', test_outputs)
        self.assertEqual(test_index_removed, si.index)

    def test_return_values(self):
        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()

        self.assertEqual(test_inputs, si.__return_values__('input'))
        self.assertEqual(test_fuzzers, si.__return_values__('fuzzer'))
        self.assertEqual(test_outputs, si.__return_values__('output'))

    def test_divide(self):
        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()

        sample_queues = si.divide(3)
        # Check whether queues are of correct sizes
        self.assertEqual(3, len(sample_queues))
        self.assertEqual(1, sample_queues[0].size())
        self.assertEqual(1, sample_queues[1].size())
        self.assertEqual(1, sample_queues[2].size())

        # Check if contents of queues resemble original sample index
        joined_index = SampleIndex.SampleIndex('test_dir')
        for ix in sample_queues:
            joined_index.index += ix.index

        self.assertListEqual(sorted(si.index, key=lambda k: k['output']),
                             sorted(joined_index.index, key=lambda k: k['output']))

        sample_queues = si.divide(2)

        # Check whether queues are of correct sizes
        self.assertEqual(2, len(sample_queues))
        self.assertEqual(2, sample_queues[0].size())
        self.assertEqual(1, sample_queues[1].size())

        # Check if contents of queues resemble original sample index
        joined_index = SampleIndex.SampleIndex('test_dir')
        for ix in sample_queues:
            joined_index.index += ix.index

        self.assertListEqual(sorted(si.index, key=lambda k: k['output']),
                             sorted(joined_index.index, key=lambda k: k['output']))

    def test_add(self):
        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()

        pre_add_index = si.index
        post_add_index = si.index + [{'input': '/file04', 'fuzzer': 'fuzz04', 'output': 'fuzz04:file04'}]

        self.assertEqual(pre_add_index, si.index)
        self.assertEqual(post_add_index, si.add('fuzz04', '/file04'))
        # The following line is intentional! It checks if add() does not add duplicate entries to the index.
        self.assertEqual(post_add_index, si.add('fuzz04', '/file04'))

    def test_add_output(self):
        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()

        pre_add_index = si.index
        post_add_index = si.index + [{'input': None, 'fuzzer': None, 'output': '/fuzz04:file04'}]

        self.assertEqual(pre_add_index, si.index)
        self.assertEqual(post_add_index, si.add_output('/fuzz04:file04'))
        # The following line is intentional! It checks if add() does not add duplicate entries to the index.
        self.assertEqual(post_add_index, si.add_output('/fuzz04:file04'))

    def test_remove_inputs(self):
        test_index_removed = [
            {'input': 1, 'fuzzer': 'fuzz01', 'output': 'fuzz01:file01'},
            {'input': 7, 'fuzzer': 'fuzz03', 'output': 'fuzz03:file03'},
        ]

        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()

        self.assertEqual(test_index_removed, si.remove_inputs([test_inputs[1]]))
        self.assertEqual([test_index_removed[1]], si.remove_inputs([test_inputs[0]]))
        self.assertEqual([], si.remove_inputs(test_inputs))

    def test_remove_fuzzers(self):
        test_index_removed = [
            {'input': 1, 'fuzzer': 'fuzz01', 'output': 'fuzz01:file01'},
            {'input': 7, 'fuzzer': 'fuzz03', 'output': 'fuzz03:file03'},
        ]

        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()

        self.assertEqual(test_index_removed, si.remove_fuzzers([test_fuzzers[1]]))
        self.assertEqual([test_index_removed[1]], si.remove_fuzzers([test_fuzzers[0]]))
        self.assertEqual([], si.remove_fuzzers(test_fuzzers))

    def test_remove_outputs(self):
        test_index_removed = [
            {'input': 1, 'fuzzer': 'fuzz01', 'output': 'fuzz01:file01'},
            {'input': 7, 'fuzzer': 'fuzz03', 'output': 'fuzz03:file03'},
        ]

        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()

        self.assertEqual(test_index_removed, si.remove_outputs([test_outputs[1]]))
        self.assertEqual([test_index_removed[1]], si.remove_outputs([test_outputs[0]]))
        self.assertEqual([], si.remove_outputs(test_outputs))

    def test_inputs(self):
        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()

        self.assertEqual(test_inputs, si.inputs())

    def test_outputs(self):
        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()

        self.assertEqual(test_outputs, si.outputs(fuzzer=None, input_file=None))
        self.assertEqual([test_outputs[1]], si.outputs(fuzzer=None, input_file=test_inputs[1]))
        self.assertEqual([test_outputs[2]], si.outputs(fuzzer=test_fuzzers[2], input_file=None))
        self.assertEqual([test_outputs[2]], si.outputs(fuzzer=test_fuzzers[2], input_file=test_inputs[2]))
        self.assertEqual(None, si.outputs(fuzzer=test_fuzzers[2], input_file=test_inputs[1]))

    def test_fuzzers(self):
        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()

        self.assertEqual(test_fuzzers, si.fuzzers())

    def test_size(self):
        si, test_inputs, test_fuzzers, test_outputs = self.prepare_SampleIndex()

        self.assertEqual(len(si.index), si.size())

        si.add('fuzz04', 'file04')
        self.assertEqual(len(si.index), si.size())
