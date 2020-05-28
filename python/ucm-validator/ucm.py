#! /usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later

# ucm.py - ALSA Use Case Manager routines
# Copyright (c) 2020 Jaroslav Kysela <perex@perex.cz>

import os
import sys
sys.path.insert(0, os.path.realpath(os.path.dirname('__file__')) + '/../lib')
from ucmlib import Ucm, UcmError, ucm_get_configs, ucm_env_get, ucm_env_put
from alsainfo import AlsaInfo
from alsajson import AlsaJson

LOG_LEVEL=1
DEBUG=False

# skip this driver
SKIP_DRIVERS=[
    'HdmiLpeAudio',
]

# skip this driver if longname does not exists
SKIP_DRIVERS2=[
    'HDA-Intel',
    'USB-Audio'
]

class Ucm2(Ucm):

    def log(self, msg, *args):
        log(msg, *args)

    def warn(self, msg, *args):
        warning(msg, *args)

    def condition_ran(self, condition_node, result, true_node, false_node, origin):

        def ee(d, k):
            if not k in d:
                d[k] = {}

        if not hasattr(self, 'conditions'):
            return

        v = repr(condition_node.value())
        r = repr(result)
        f = origin and origin.shortfn() or self.shortfn()
        id = condition_node.full_id()
        ee(self.conditions, f)
        ee(self.conditions[f], v)
        d = self.conditions[f][v]
        d['id'] = id
        d[r] = 1
        if true_node is None or true_node.is_empty():
            d[repr(True)] = 1
        if false_node is None or false_node.is_empty():
            d[repr(False)] = 1

def error1(msg, *args):
    sys.stderr.write('ERR: ')
    sys.stderr.write(msg % args + '\n')    

def error(lvl, msg, *args):
    sys.stderr.write(msg % args + '\n')
    sys.exit(lvl)

def warning(msg, *args):
    sys.stderr.write('WARN: ' + ((msg % args) + '\n'))

def log(lvl, msg, *args):
    if LOG_LEVEL >= lvl:
        sys.stdout.write(msg % args + '\n')

def env(filename, lvl=0):
    filename = os.path.abspath(filename)
    path = filename
    while lvl > 0:
        path = os.path.split(path)[0]
        lvl -= 1
    ucm_env_get(path)

def do_one(*args):
    env(args[0], 2)
    c = Ucm2()
    c.load(args[0])

def do_all(*args):

    def pp(filename):
        c = Ucm2()
        c.load(filename)

    if len(args) == 0:
        error(1, 'Specify root directory with ucm configuration files.')

    env(args[0])
    cs = ucm_get_configs(args[0])
    for c in cs:
        pp(c)

def do_configs(*args):

    def config_walk(path1):
        errors = 0
        warnings = 0
        for file in os.listdir(path1):
            if file.startswith('.'):
                continue
            path2 = path1 + '/' + file
            if os.path.isdir(path2):
                errors1, warnings1 = config_walk(path2)
                errors += errors1
                warnings += warnings1
                continue
            if not file.endswith('.txt') and not file.endswith('.json') and \
               not file.endswith('.py'):
                continue
            info = file.endswith('.txt') and AlsaInfo() or AlsaJson()
            if filter and not path2 in filter:
                continue
            info.load(path2)
            for cardnum in info.cards:
                card = info.cards[cardnum]
                if card.driver in SKIP_DRIVERS:
                    continue
                c = Ucm2(verify=card)
                for l in c.get_file_list(ucm_path):
                    if os.path.exists(l):
                        break
                    l = None
                if not l:
                    if card.driver in SKIP_DRIVERS2:
                        continue
                    warnings += 1
                    warning('Unable to find UCM configuration for %s', repr(path2))
                    idx = 0
                    for l in c.get_file_list(ucm_path):
                        warning('  Path#%s: %s', idx, repr(l))
                        idx += 1
                    continue
                c.conditions = conditions
                c.load(l)
                paths.append(c.shortfn())
                try:
                    c.check()
                except UcmError as e:
                    error1(str(e))
                    error1('  ' + repr(card))
                    errors += 1
                if LOG_LEVEL > 255:
                    sys.stdout.write(c.dump())
        return errors, warnings

    paths = []
    ucm_path = args[0]
    env(ucm_path)
    alsainfo_path = args[1]
    filter = args[2:]
    conditions = {}
    errors, warnings = config_walk(alsainfo_path)
    # check, if all configuration files were handled
    cs = ucm_get_configs(args[0], short=True, link=False)
    for c in cs:
        if filter and alsainfo_path + '/' + c != filter:
            continue
        if not c in paths:
            error1('%s: no alsa-info files!', c)
            errors += 1
    # check, if all conditions were executed
    for filename in conditions:
        for cond in conditions[filename]:
            v = conditions[filename][cond]
            if not ('True' in v and 'False' in v):
                what = 'True' in v and 'False' or 'True'
                error1('%s: %s - %s block not executed', filename, v['id'], what)
                errors += 1
    if warnings > 0:
        warning('total warnings: %s' % warnings)
    if errors > 0:
        error1('total errors: %s' % errors)
    return errors and 1 or 0

def do_unknown(*args):
    r = 'Please, specify a valid command:\n'
    for n in globals():
        if n.startswith('do_') and n != 'do_unknown':
            r += '  ' + n[3:] + '\n'
    error(1, r[:-1])

def main(argv):
    global DEBUG, LOG_LEVEL
    if len(argv) > 1:
        while 1:
            if argv[1] == '--debug':
                DEBUG=True
                argv.pop(0)
                continue
            elif argv[1] == '--level':
                LOG_LEVEL=int(argv[2])
                argv.pop(0)
                argv.pop(0)
                continue
            break
    cmd = 'do_' + (len(argv) > 1 and argv[1] or 'unknown')
    if cmd in globals():
        r = globals()[cmd](*argv[2:])
        sys.exit(r is None and 0 or r)
    do_unknown()

if __name__ == "__main__":
    main(sys.argv)
