"""
Copyright 2015-2016 @_rc0r <hlt99@blinkenshell.org>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os


class SampleIndex:
    def __init__(self, output_dir, index=None, min_filename=False, omit_fuzzer_name=False):
        self.output_dir = os.path.abspath(output_dir)
        if index is not None:
            self.index = index
        else:
            self.index = []
        self.min_filename = min_filename
        self.omit_fuzzer_name = omit_fuzzer_name

    def __generate_output__(self, fuzzer, input_file):
        input_filename = os.path.basename(input_file)
        fuzzer_name = os.path.basename(fuzzer)
        if self.min_filename:
            try:
                input_filename = input_filename.split(",")[0].split(":")[1]
            except Exception:
                pass
        if self.omit_fuzzer_name:
            return input_filename
        else:
            return "%s:%s" % (fuzzer_name, input_filename)

    def __remove__(self, key, values):
        self.index = [x for x in self.index if x[key] not in values]
        return self.index

    def __return_values__(self, key):
        return [v[key] for v in self.index]

    def divide(self, count):
        """
        Divide sample index into approx. equally sized parts.

        :param count:   Number of parts
        :return:        List containing divided sample indexes
        """
        indexes = [self.index[i::count] for i in range(count)]
        sample_indexes = []
        for i in indexes:
            sample_indexes.append(SampleIndex(self.output_dir, i))

        return sample_indexes

    def add(self, fuzzer, input_file):
        sample_output = self.__generate_output__(fuzzer, input_file)
        # avoid to add duplicates (by filename) to sample index
        # #TODO: Speed this up, if possible
        if sample_output not in self.outputs():
            self.index.append({
                'input': os.path.abspath(os.path.expanduser(input_file)),
                'fuzzer': fuzzer,
                'output': sample_output})
        return self.index

    def add_output(self, output_file):
        output_file = os.path.abspath(output_file)
        # avoid to add duplicates to index
        if output_file not in self.outputs():
            # we can't generate input filenames, fuzzer from output filenames,
            # so leave them blank
            self.index.append({
                'input': None,
                'fuzzer': None,
                'output': output_file})
        return self.index

    def remove_inputs(self, input_files):
        self.index = self.__remove__("input", input_files)
        return self.index

    def remove_fuzzers(self, fuzzers):
        self.index = self.__remove__("fuzzer", fuzzers)
        return self.index

    def remove_outputs(self, output_files):
        self.index = self.__remove__("output", output_files)
        return self.index

    def inputs(self):
        return self.__return_values__("input")

    def outputs(self, fuzzer=None, input_file=None):
        if fuzzer is not None and input_file is not None:
            for i in self.index:
                if i['fuzzer'] == fuzzer and i['input'] == input_file:
                    return [i['output']]
        elif fuzzer is not None:
            return [i['output'] for i in self.index if i['fuzzer'] == fuzzer]
        elif input_file is not None:
            return [i['output'] for i in self.index if i['input'] == input_file]
        else:
            return self.__return_values__("output")

    def fuzzers(self):
        return self.__return_values__("fuzzer")

    def size(self):
        return len(self.index)
