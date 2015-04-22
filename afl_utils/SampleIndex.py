"""
Copyright 2015 @_rc0r <hlt99@blinkenshell.org>

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
    def __init__(self, output_dir):
        self.output_dir = os.path.abspath(output_dir)
        self.index = []

    def __generate_output__(self, fuzzer, input_file):
        return "%s:%s" % (fuzzer, os.path.basename(input_file))

    def __remove__(self, key, values):
        self.index = [x for x in self.index if x[key] not in values]
        return self.index

    def __return_values__(self, key):
        return [v[key] for v in self.index]

    def add(self, fuzzer, input_file):
        self.index.append({
            'input': os.path.abspath(input_file),
            'fuzzer': fuzzer,
            'output': self.__generate_output__(fuzzer, input_file)})
        return self.index

    def add_output(self, output_file):
        # we can't generate input filenames, fuzzer from output filenames,
        # so leave them blank
        self.index.append({
            'input': None,
            'fuzzer': None,
            'output': os.path.abspath(output_file)})
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

    def outputs(self):
        return self.__return_values__("output")

    def fuzzers(self):
        return self.__return_values__("fuzzer")