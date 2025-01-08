#! /usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later

# ucm.py - ALSA Use Case Manager routines
# Copyright (c) 2025 Jaroslav Kysela <perex@perex.cz>

import os
import sys
import re
import inspect
import argparse
sys.path.insert(0, f'{os.path.realpath(os.path.dirname("__file__"))}/../lib')
from aconfig import AlsaConfig

LOG_LEVEL=1
DEBUG=False

VALID_DEVICE_NAMES = {
    'Speaker',
    'Line',
    'Mic',
    'Headphones',
    'Headset',
    'Handset',
    'Bluetooth',
    'Earpiece',
    'SPDIF',
    'HDMI',
    'USB',
    'Direct',
}

class UcmError(Exception):
    """Indicates exceptions raised by a AlsaConfig class."""
    pass

class AllUcmFiles:

    def __init__(self, ucm_path):
        os.environ['ALSA_CONFIG_DIR'] = os.path.abspath(os.path.realpath(ucm_path))
        os.chdir(ucm_path)
        self.files = self.tree_files_with_filter('.', filter=lambda x: x.endswith('.conf'))

    def __iter__(self):
        return self.files.__iter__()

    @staticmethod
    def tree_files_with_filter(ucm_path, filter=None, hidden=False):
        r = []
        for path, dirnames, filenames in os.walk(ucm_path):
            for f in filenames:
                if not hidden and f[0] == '.':
                    continue
                full = f'{path}/{f}'
                if os.path.isdir(full):
                    continue
                if filter and not filter(full):
                    continue
                r.append(full)
        return r

class ReportState:

    def __init__(self):
        self.errors = 0
        self.warnings = 0

    @staticmethod
    def output(stdout, filename, fmt, **kwargs):
        stdout.write(f'{filename}: {fmt.format(kwargs)}\n')

    def warning(self, filename, fmt, **kwargs):
        self.warnings += 1
        self.output(sys.stdout, filename, fmt, **kwargs)

    def exc_warning(self, filename, msg, exc):
        self.warning(filename, f'{msg}: {exc}', exc=exc)

    def error(self, filename, fmt, **kwargs):
        self.errors += 1
        self.output(sys.stderr, filename, fmt, **kwargs)

    def exc_error(self, filename, msg, exc):
        self.error(filename, f'{msg}: {exc}', exc=exc)

    def report(self):
        if self.warnings > 0:
            sys.stdout.write(f'total warnings: {self.warnings}\n')
        if self.errors > 0:
            sys.stderr.write(f'total errors: {self.errors}\n')

class BasicVerification:

    def __init__(self, state, filename):
        self.state = state
        self.filename = filename
        self.load_check()
        if os.path.exists(filename):
            self.contents = open(filename).read()
            self.indentation_check()

    def load_check(self):

        def SectionDeviceVerify(node):
            if node.id[0] == '$':
                return
            m = re.match(r"(?P<base>[a-zA-Z]+)[ ]{0,1}(?P<index>[0-9]*)", node.id)
            d = m.groupdict(m)
            if not d['base'] in VALID_DEVICE_NAMES:
                self.state.error(self.filename, f'Device name {node.id} /{node.full_id()}/ is not valid (see https://github.com/alsa-project/alsa-lib/blob/master/include/use-case.h)')

        def walk(node):
            if node.id == 'SectionDevice':
                if not node.is_compound():
                    if node.parent.id in ('Before', 'After'):
                        return
                    self.state.error(self.filename, f'SectionDevice {node.full_id()} should be compound! ({node.value()})')
                for c in node:
                    SectionDeviceVerify(c)
                return
            if node.is_compound():
                for c in node:
                    walk(c)

        try:
            ac = AlsaConfig()
            ac.load(self.filename)
        except BaseException as exc:
            self.state.exc_error(self.filename, "ALSA configuration load error", exc)
            return
        try:
            walk(ac)
        except BaseException as exc:
            self.state.exc_error(self.filename, "UCM error", exc)
            return

    def indentation_check(self):
        lineno = 1
        for line in self.contents.splitlines():
            if line.startswith(' ') and (line.startswith('  ') or len(line) < 3):
                self.state.error(f'{self.filename}:{lineno}', 'Wrong indentation (use tabs to save space!)')
            if line.endswith(' ') or line.endswith('\t'):
                self.state.error(f'{self.filename}:{lineno}', 'Trailing space or tabelator!')
            lineno += 1

class Verify:

    def __init__(self, ns):
        self.ns = ns

    def basic_verification(self):
        state = ReportState()
        for f in AllUcmFiles(ns.ucmdir):
            BasicVerification(state, f)
        state.report()
        return state.errors and 1 or 0

def do_unknown(*args):
    r = 'Please, specify a valid command:\n'
    for n in globals():
        if n.startswith('do_') and n != 'do_unknown':
            r += '  ' + n[3:] + '\n'
    error(1, r[:-1])

class BaseCommand:

    def __init__(self, name):
        self.name = name

    @staticmethod
    def exit(code):
        sys.exit(code)

class CommandConfigs(BaseCommand):

    def arguments(self, subparser):
        parser = subparser.add_parser(self.name, help='Verify configurations (basic)')
        parser.add_argument('-l', '--level', default=0, help='Verbosity level (0-255)')
        parser.add_argument('-u', '--ucmdir', default=None, help='UCM configuration directory')

    def run(self, ns):
        self.exit(Verify(ns).basic_verification())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='UCM configuration validator')
    subparser = parser.add_subparsers(title='Commands', dest='command')
    class_list = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    class_dict = {}
    for name, obj in class_list:
        if name.startswith('Command') and issubclass(obj, BaseCommand):
            n = name[7:].lower()
            class_dict[n] = o = obj(n)
            o.arguments(subparser)
    ns = parser.parse_args()
    if not ns.command:
        print(f'Available commands: {list(class_dict.keys())}')
        sys.exit(1)
    ns.script_file = os.path.abspath(__file__)
    obj = class_dict[ns.command]
    obj.run(ns)
