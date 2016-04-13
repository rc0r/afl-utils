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

import afl_utils
from afl_utils.AflPrettyPrint import clr, print_ok, print_warn, print_err

import argparse
import os
import sys
import subprocess

_rsync_default_options = ['-racz']


class AflBaseSync(object):
    def __init__(self, server_config, fuzzer_config):
        self.server_config = server_config
        self.fuzzer_config = fuzzer_config


class AflRsync(AflBaseSync):
    def __prepare_rsync_commandline(self, local_path, remote_path, rsync_options=list(_rsync_default_options),
                                    rsync_excludes=list([]), rsync_get=False):
        cmd = ['rsync']

        cmd = cmd + [o for o in rsync_options]
        cmd = cmd + ['--exclude=\"{}\"'.format(e) for e in rsync_excludes]
        if rsync_get:
            cmd = cmd + '{1}/* {0}/'.format(local_path, remote_path).split()
        else:
            cmd = cmd + '{0}/ {1}.sync/'.format(local_path, remote_path).split()

        return cmd

    def __invoke_rsync(self, rsync_cmdline):
        ret = True
        try:
            subprocess.check_call(' '.join(rsync_cmdline), shell=True)
        except subprocess.CalledProcessError as e:
            print_err('rsync failed with exit code {}'.format(e.returncode))
            ret = False
        return ret

    def __get_fuzzers(self):
        fuzzers = os.listdir(self.fuzzer_config['sync_dir'])

        # strip pulled dirs
        fuzzers = (fuzzer for fuzzer in fuzzers if not fuzzer.endswith('.sync'))
        return fuzzers

    def rsync_put(self, local_path, remote_path, rsync_options=list(_rsync_default_options), rsync_excludes=list([])):
        cmd = self.__prepare_rsync_commandline(local_path, remote_path, rsync_options, rsync_excludes)
        return self.__invoke_rsync(cmd)

    def rsync_get(self, remote_path, local_path, rsync_options=list(_rsync_default_options), rsync_excludes=list([])):
        cmd = self.__prepare_rsync_commandline(local_path, remote_path, rsync_options, rsync_excludes, True)
        return self.__invoke_rsync(cmd)

    def push(self):
        fuzzers = self.__get_fuzzers()

        # restrict to certain session, if requested
        if self.fuzzer_config['session'] is not None:
            fuzzers = (fuzzer for fuzzer in fuzzers if fuzzer.startswith(self.fuzzer_config['session']))

        excludes = []

        if self.fuzzer_config['exclude_crashes']:
            excludes += ['crashes*/']

        if self.fuzzer_config['exclude_hangs']:
            excludes += ['hangs*/']

        for f in fuzzers:
            local_path = os.path.join(self.fuzzer_config['sync_dir'], f)
            remote_path = os.path.join(self.server_config['remote_path'], f)
            print_ok('Pushing {} -> {}.sync'.format(local_path, remote_path))
            self.rsync_put(local_path, remote_path, rsync_excludes=excludes)

    def pull(self):
        fuzzers = self.__get_fuzzers()

        local_path = self.fuzzer_config['sync_dir']
        remote_path = self.server_config['remote_path']

        options = list(_rsync_default_options)
        excludes = []

        # exclude our previously pushed fuzzer states from being pulled again
        for fuzzer in fuzzers:
            excludes += ['{}.sync'.format(fuzzer)]

        # restrict to certain session, if requested
        if self.fuzzer_config['session'] is not None:
            options += ['--include=\"/{}*/\"'.format(self.fuzzer_config['session'])]
            excludes += ['*']

        print_ok('Pulling {}/* <- {}/'.format(local_path, remote_path))
        self.rsync_get(remote_path, local_path, rsync_options=options, rsync_excludes=excludes)

    def sync(self):
        self.pull()
        self.push()


def show_info():
    print(clr.CYA + 'afl-sync ' + clr.BRI + '{}'.format(afl_utils.__version__) + clr.RST + ' by {}'.format(afl_utils.__author__))
    print('Synchronize fuzzer states with a remote location.')
    print('')


def main(argv):
    show_info()

    parser = argparse.ArgumentParser(description='afl-sync synchronizes fuzzer state directories between different \
locations. Supported are remote transfers through rsync that may use transport compression.', 
                                     usage='afl-sync [-S SESSION] <cmd> <src_sync_dir> <dst_storage_dir>')

    parser.add_argument('cmd',
                        help='Command to perform: push, pull or sync. Push transmits the local state from '
                             '<src_sync_dir> to the destination <dst_storage_dir>. Pull fetches remote state(s) into '
                             'the local synchronization dir appending the \'.sync\' extension. Sync performs a '
                             'pull operation followed by a push.')
    parser.add_argument('src_sync_dir',
                        help='Source afl synchronisation directory containing state directories of afl instances.')
    parser.add_argument('dst_storage_dir',
                        help='Destination directory used as fuzzer state storage. This shouldn\'t be an afl sync dir!')
    parser.add_argument('-S', '--session', dest='session', default=None,
                        help='Name of an afl-multicore session. If provided, only fuzzers belonging to '
                             'the specified session will be synced with the destination. Otherwise state '
                             'directories of all fuzzers inside the synchronisation dir will be exchanged. '
                             'Directories ending on \'.sync\' will never be pushed back to the destination!')

    args = parser.parse_args(argv[1:])

    args.cmd = args.cmd.lower()
    if not args.cmd in ['push', 'pull', 'sync']:
        print_err('Sorry, unknown command requested!')
        sys.exit(1)

    if not os.path.exists(args.src_sync_dir):
        if args.cmd in ['pull', 'sync']:
            print_warn('Local afl sync dir does not exist! Will create it for you!')
            os.makedirs(args.src_sync_dir)
        else:
            print_err('Local afl sync dir does not exist!')
            sys.exit(1)

    server_config = {
        'remote_path':      args.dst_storage_dir,
    }

    fuzzer_config = {
        'sync_dir':         args.src_sync_dir,
        'session':          args.session,
        'exclude_crashes':  False,
        'exclude_hangs':    False,
    }

    rsyncEngine = AflRsync(server_config, fuzzer_config)

    if args.cmd == 'push':
        rsyncEngine.push()
    elif args.cmd == 'pull':
        rsyncEngine.pull()
    elif args.cmd == 'sync':
        rsyncEngine.sync()


if __name__ == "__main__":
    main(sys.argv)
