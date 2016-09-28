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
import sqlite3 as lite

from afl_utils.AflPrettyPrint import *


class sqliteConnector:

    def __init__(self, database_path, verbose=True):
        self.database_path = database_path
        self.dbcon = lite.connect(database_path, isolation_level='Exclusive')
        self.dbcur = self.dbcon.cursor()
        self.dbcur.execute('PRAGMA synchronous = 0')
        # self.dbcur.execute('PRAGMA journal_mode = OFF')
        self.verbose = verbose

    def init_database(self, table, table_spec):
        """
        Prepares a sqlite3 database for data set storage. If the file specified in database_path doesn't exist a new
        sqlite3 database with table 'Data' will be created. Otherwise the existing database is used to store additional
        data sets.

        DO NOT USE WITH USER SUPPLIED `table` AND `table_spec` PARAMS!
        !!! THIS METHOD IS *NOT* SQLi SAFE !!!

        :param table:       Name of the table to create.
        :param table_spec:  String containing the SQL table specification
        :return: None
        """
        table_data_exists = False
        if os.path.isfile(self.database_path):
            try:
                self.dbcur.execute("SELECT Count(*) FROM {}".format(table))
                if self.verbose:
                    print_warn("Using existing database to store results, %s entries in this database so far." %
                          str(self.dbcur.fetchone()[0]))
                table_data_exists = True
            except lite.OperationalError:
                if self.verbose:
                    print_warn("Table \'{}\' not found in existing database!".format(table))

        if not table_data_exists:   # If the database doesn't exist, we'll create it.
            if self.verbose:
                print_ok("Creating new table \'{}\' in database \'{}\' to store data!".format(table, self.database_path))
            self.dbcur.execute("CREATE TABLE `{}` ({})".format(table, table_spec))

    def dataset_exists(self, table, dataset, compare_field):
        """
        Check if dataset was already submitted into database.

        :param dataset: A dataset dict consisting of sample filename, sample classification and classification
                        description.
        :return:        True if the data set is already present in database, False otherwise.
        """
        # The nice thing about using the SQL DB is that I can just have it make
        # a query to make a duplicate check. This can likely be done better but
        # it's "good enough" for now.
        output = False

        # check sample by its name (we could check by hash to avoid dupes in the db)
        qstring = "SELECT * FROM {} WHERE {} IS ?".format(table, compare_field)
        self.dbcur.execute(qstring, (dataset[compare_field],))
        if self.dbcur.fetchone() is not None:  # We should only have to pull one.
            output = True

        return output

    def insert_dataset(self, table, dataset):
        """
        Insert a dataset into the database.

        DO NOT USE WITH USER SUPPLIED `table` AND `table_spec` PARAMS!
        !!! THIS METHOD IS *NOT* SQLi SAFE !!!

        :param table:   Name of the table to insert data into.
        :param dataset: A dataset dict consisting of sample filename, sample classification and classification
                        description.
        :return:        None
        """
        # Just a simple function to write the results to the database.
        if len(dataset) <= 0:
            return

        field_names_string = ", ".join(["`{}`".format(k) for k in dataset.keys()])
        field_values_string = ", ".join(["'{}'".format(v) for v in dataset.values()])
        qstring = "INSERT INTO {} ({}) VALUES({})".format(table, field_names_string, field_values_string)
        self.dbcur.execute(qstring)

    def commit_close(self):
        """
        Write database changes to disk and close cursor and connection.

        :return:    None
        """
        self.dbcon.commit()
        self.dbcur.close()
        self.dbcon.close()
