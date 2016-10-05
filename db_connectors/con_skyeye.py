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

import uuid
from db_connectors.con_sqlite import sqliteConnector


class SkyEyeConnector(sqliteConnector):
    def __init__(self, database_path, verbose=True):
        self.table_index = 'aflutils_index'
        self.table_fuzzers = 'aflutils_fuzzers'
        self.table_stats = 'aflutils_stats'
        self.table_results = 'aflutils_results'

        self.schema_index = """"job" char(32) NOT NULL PRIMARY KEY, "sync_dir" varchar(500) NOT NULL UNIQUE"""

        self.schema_fuzzers = """"id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "fuzzer" varchar(200) NOT NULL,
"command_line" varchar(1000) NOT NULL, "afl_banner" varchar(200) NOT NULL, "afl_version" varchar(10) NOT NULL,
"job_id" char(32) NOT NULL REFERENCES "aflutils_index" ("job"), "fuzzer_pid" integer NULL"""

        self.schema_stats = """"id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "start_time" integer NOT NULL,
"last_update" integer NOT NULL, "cycles_done" integer NOT NULL, "execs_done" integer NOT NULL,
"execs_per_sec" real NOT NULL, "paths_total" integer NOT NULL, "paths_favored" integer NOT NULL,
"paths_found" integer NOT NULL, "paths_imported" integer NOT NULL, "max_depth" integer NOT NULL,
"cur_path" integer NOT NULL, "pending_favs" integer NOT NULL, "pending_total" integer NOT NULL,
"variable_paths" integer NOT NULL, "stability" real NOT NULL, "bitmap_cvg" real NOT NULL,
"unique_crashes" integer NOT NULL, "unique_hangs" integer NOT NULL, "last_path" integer NOT NULL,
"last_crash" integer NOT NULL, "last_hang" integer NOT NULL, "execs_since_crash" integer NOT NULL,
"exec_timeout" integer NOT NULL, "fuzzer_id" integer NOT NULL REFERENCES "aflutils_fuzzers" ("id")"""

        self.schema_results = """"id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "sample" varchar(500) NOT NULL,
"classification" varchar(100) NOT NULL, "classification_description" varchar(200) NOT NULL,
"hash" varchar(65) NOT NULL, "comment" varchar(1000) NOT NULL,
"fuzzer_id" integer NOT NULL REFERENCES "aflutils_fuzzers" ("id")"""

        super(SkyEyeConnector, self).__init__(database_path, verbose)

    def init_database(self):
        super(SkyEyeConnector, self).init_database(self.table_index, self.schema_index)
        super(SkyEyeConnector, self).init_database(self.table_fuzzers, self.schema_fuzzers)
        super(SkyEyeConnector, self).init_database(self.table_stats, self.schema_stats)
        super(SkyEyeConnector, self).init_database(self.table_results, self.schema_results)

    def job_id(self, sync_dir, create=True):
        """
        Create or retrieve the job uuid for the provided sync dir.

        :param sync_dir:    afl-fuzz synchronisation dir
        :type sync_dir:     str
        :param create:      Create database entry if not found
        :type create:       bool
        :return:            job uuid or None
        """
        dataset = {
            'job': uuid.uuid4(),
            'sync_dir': sync_dir
        }
        data = self.dataset(self.table_index, dataset, ['sync_dir'])
        job_id = None

        if len(data) == 0 or data is None:
            if create:
                self.insert_dataset(self.table_index, dataset)
                job_id = dataset['job']
        else:
            job_id = data[0][0]

        return job_id

    def fuzzer_id(self, fuzzer_dataset, create=True):
        data = self.dataset(self.table_fuzzers, fuzzer_dataset, ['job_id', 'fuzzer'])
        fuzzer_id = None

        if len(data) == 0 or data is None:
            if create:
                self.insert_dataset(self.table_fuzzers, fuzzer_dataset)
                data = self.dataset(self.table_fuzzers, fuzzer_dataset, ['job_id', 'fuzzer'])

        fuzzer_id = data[0][0]
        return fuzzer_id
