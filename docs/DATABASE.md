# afl-utils database schema

## Table 'aflutils_index'

Contains a unique id for each fuzzing job (generated whenever `afl-multicore start` is called).

id: pk, int, autoincrement
uuid: uuid, unique; job id

    id | uuid
    ---+--------
    0  | <uuid>

## Table 'aflutils_fuzzers'

Contains general (quite static) information of the fuzzers known to afl-utils. Info is collected whenever
`afl-multicore start` is called or `afl-stats` detects new fuzzers in a sync dir.

id: pk, int, autoincrement
uuid: fk, uuid; `aflutil_index.uuid` job id of the fuzzing job the fuzzer belongs to
fuzzer: varchar(200); session name of the fuzzer as set in `afl-multicore.conf` (aka fuzzer name) 
command_line: varchar(1000); afl-fuzz command line
afl_version: varchar(10); afl-fuzz version used
afl_banner: varchar(200); afl-fuzz banner set in `afl-multicore.conf`

    id | uuid | fuzzer | command_line | afl_version | afl_banner
    ---+------+--------+--------------+-------------+------------
    0  | 12.. | tar000 | afl-fuzz ... | 2.35b       | target

## Table 'aflutils_stats'

Contains highly variable information from `fuzzer_stats`. Whenever `afl-stats` is executed a new entry
is added to this table (unless the fuzzer is offline and nothing has changed).

id: pk, int, autoincrement
fuzzer_id: fk?, int; `aflutils_fuzzers.id` identifying the fuzzer
*stats: see afl-stats

    id | fuzzer_id | *stats ...
    ---+-----------+------------
    0  | 0         | ...

## Table 'aflutils_results'

Contains triage information collected by `afl-collect`.

id: pk, int, autoincrement
fuzzer_id: fk?, int; `aflutils_fuzzer.id` identifying the fuzzer
sample: varchar(500); filename of the sample
classification: varchar(100); exploitability classification returned by `exploitable`
classification_description: varchar(200); exploitability classification description
hash: varchar(65); hash of stack trace returned by `exploitable`
comment: varchar(1000); field for user comments

    id | fuzzer_id | sample | classification | classification_description | hash | comment
    ---+-----------+--------+----------------+----------------------------+------+--------------------
    0  | 0         | cra... | EXPLOITABLE    | StackCorruption (X/Y)      | a... | reported as #12345
    
