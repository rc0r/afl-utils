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
import subprocess

import afl_utils

import threading


class VerifyThread(threading.Thread):
    def __init__(self, thread_id, target_cmd, in_queue, out_queue, in_queue_lock, out_queue_lock):
        threading.Thread.__init__(self)
        self.id = thread_id
        self.target_cmd = target_cmd
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.in_queue_lock = in_queue_lock
        self.out_queue_lock = out_queue_lock
        self.exit = False

    def run(self):
        if afl_utils.afl_collect.stdin_mode(cmd_string):
            cmd_string += " < @@"

        while not self.exit:
            self.in_queue_lock.acquire()
            if not self.in_queue.empty():
                cs = self.in_queue.get()
                self.in_queue_lock.release()

                cmd = cmd_string.replace("@@", os.path.abspath(cs))
                try:
                    v = subprocess.call(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True, timeout=60)
                    # check if process was terminated/stopped by signal
                    if not os.WIFSIGNALED(v) and not os.WIFSTOPPED(v):
                        self.out_queue_lock.acquire()
                        self.out_queue.put(cs)
                        self.out_queue_lock.release()
                    else:
                        # need extension (add uninteresting signals):
                        # following signals don't indicate hard crashes: 1
                        # os.WTERMSIG(v) ?= v & 0x7f ???
                        if (os.WTERMSIG(v) or os.WSTOPSIG(v)) in [1]:
                            self.out_queue_lock.acquire()
                            self.out_queue.put(cs)
                            self.out_queue_lock.release()
                        # debug
                        #else:
                        #    if os.WIFSIGNALED(v):
                        #        print("%s: sig: %d (%d)" % (cs, os.WTERMSIG(v), v))
                        #    elif os.WIFSTOPPED(v):
                        #        print("%s: sig: %d (%d)" % (cs, os.WSTOPSIG(v), v))
                except Exception:
                    pass
            else:
                self.in_queue_lock.release()
                self.exit = True


class GdbThread(threading.Thread):
    def __init__(self, thread_id, gdb_cmd, out_dir, grep_for, out_queue, out_queue_lock):
        threading.Thread.__init__(self)
        self.id = thread_id
        self.gdb_cmd = gdb_cmd
        self.out_dir = out_dir
        self.out_queue = out_queue
        self.out_queue_lock = out_queue_lock
        self.grep_for = grep_for

    def run(self):
        try:
            script_output = subprocess.check_output(" ".join(self.gdb_cmd), shell=True, stderr=subprocess.DEVNULL,
                                                    stdin=subprocess.DEVNULL, universal_newlines=True)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            script_output = e.output

        script_output = script_output.splitlines()

        for line in script_output:
            matching = [line.replace(g, '') for g in self.grep_for if g in line]
            matching = " ".join(matching).strip('\' ')
            matching = matching.replace(self.out_dir, '')
            if len(matching) > 0:
                self.out_queue_lock.acquire()
                self.out_queue.put(matching)
                self.out_queue_lock.release()
