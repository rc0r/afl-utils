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

import sys
import subprocess

#from paramiko import SSHClient, AutoAddPolicy
#from scp import SCPClient


class AflBaseSync(object):
    def __init__(self, server_config, fuzzer_config):
        self.server_config = server_config
        self.fuzzer_config = fuzzer_config


class AflRsync(AflBaseSync):
    def __prepare_rsync_commandline(self, local_path, remote_path, rsync_options=list(['-ra']),
                                    rsync_excludes=list([]), rsync_get=False):
        cmd = ['rsync']

        cmd = cmd + [o for o in rsync_options]
        cmd = cmd + ['--exclude=\"{}\"'.format(e) for e in rsync_excludes]
        if rsync_get:
            cmd = cmd + '{1}/ {0}/'.format(local_path, remote_path).split()
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

    def rsync_put(self, local_path, remote_path, rsync_options=list(['-raz']), rsync_excludes=list([])):
        cmd = self.__prepare_rsync_commandline(local_path, remote_path, rsync_options, rsync_excludes)
        return self.__invoke_rsync(cmd)

    def rsync_get(self, local_path, remote_path, rsync_options=list(['-raz']), rsync_excludes=list([])):
        cmd = self.__prepare_rsync_commandline(local_path, remote_path, rsync_options, rsync_excludes, True)
        return self.__invoke_rsync(cmd)

    def sync(self):
        pass


def show_info():
    print(clr.CYA + "afl-sync " + clr.BRI + "%s" % afl_utils.__version__ + clr.RST + " by %s" % afl_utils.__author__)
    print("Synchronize fuzzer states with a remote location.")
    print("")


def main(argv):
    show_info()
    sync = AflRsync(None, None)


if __name__ == "__main__":
    main(sys.argv)
