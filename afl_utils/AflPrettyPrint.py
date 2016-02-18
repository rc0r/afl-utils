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


class clr:
    # taken from AFL's debug.h
    BLK = "\x1b[0;30m"
    RED = "\x1b[0;31m"
    GRN = "\x1b[0;32m"
    BRN = "\x1b[0;33m"
    BLU = "\x1b[0;34m"
    MGN = "\x1b[0;35m"
    CYA = "\x1b[0;36m"
    NOR = "\x1b[0;37m"
    GRA = "\x1b[1;30m"
    LRD = "\x1b[1;31m"
    LGN = "\x1b[1;32m"
    YEL = "\x1b[1;33m"
    LBL = "\x1b[1;34m"
    PIN = "\x1b[1;35m"
    LCY = "\x1b[1;36m"
    BRI = "\x1b[1;37m"
    RST = "\x1b[0m"


def print_ok(msg_str):
    print("{0}[*] {1}{2}".format(clr.LGN, clr.RST, msg_str))


def print_warn(msg_str):
    print("{0}[!] {1}{2}".format(clr.YEL, clr.RST, msg_str))


def print_err(msg_str):
    print("{0}[!] {1}{2}".format(clr.LRD, clr.RST, msg_str))
