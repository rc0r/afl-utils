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

import argparse
import json
import sys
import time

import afl_utils
from afl_utils.AflPrettyPrint import clr, print_ok, print_warn, print_err


class AflCronDaemon(object):
    def __init__(self, config_file, quiet=False):
        self.config = self.load_config(config_file)
        self.quiet = quiet

    def load_config(self, config_file):
        with open(config_file, 'r') as raw_config:
            config = json.load(raw_config)
        return config

    def get_module(self, module_path):
        module_name = module_path.rsplit('.', 1)[1]
        try:
            module = __import__(module_path, fromlist=[module_name])
        except ImportError:
            raise ValueError('Module \'{}\' could not be imported' .format(module_path,))
        return module

    def get_class(self, module, class_name):
        try:
            cls = getattr(module, class_name)
        except AttributeError:
            raise ValueError('Module \'{}\' has no class \'{}\''.format(module, class_name,))
        return cls

    def run_job(self, job):
        job_module = self.get_module(job['module'])
        job_args = [job['module'].rsplit('.', 1)[1]] + job['params'].split()
        if not self.quiet:
            print_ok('Executing \'{}\' ({})'.format(job['name'], job['module']))
        job_module.main(job_args)

    def run(self):
        doExit = False
        while not doExit:
            try:
                for job in self.config['jobs']:
                    self.run_job(job)

                if float(self.config['interval']) < 0:
                    doExit = True
                else:
                    time.sleep(float(self.config['interval']) * 60)
            except KeyboardInterrupt:
                print('\b\b')
                print_ok('Aborted by user. Good bye!')
                doExit = True


def show_info():
    print(clr.CYA + 'afl-cron ' + clr.BRI + '%s' % afl_utils.__version__ + clr.RST + ' by %s' % afl_utils.__author__)
    print('Periodically run tools from the afl-utils collection.')
    print('')


def main(argv):
    parser = argparse.ArgumentParser(description='Post selected contents of fuzzer_stats to Twitter.',
                                     usage='afl-stats [-c config] [-d] [-h] [-q]\n')

    parser.add_argument('-c', '--config', dest='config_file',
                        help='afl-stats config file (Default: afl-stats.conf)!', default='afl-cron.conf')
    parser.add_argument('-d', '--daemon', dest='daemon', action='store_const', const=True,
                        help='Daemon mode: run in background', default=False)
    parser.add_argument('-q', '--quiet', dest='quiet', action='store_const', const=True,
                        help='Suppress any output', default=False)

    args = parser.parse_args(argv[1:])

    if not args.quiet and not args.daemon:
        show_info()

    cron = AflCronDaemon(args.config_file, quiet=args.quiet)
    cron.run()


if __name__ == "__main__":
    main(sys.argv)
