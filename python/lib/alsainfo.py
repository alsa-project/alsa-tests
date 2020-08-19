#! /usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later

# alsainfo.py - ALSA alsa-info.sh output parser
# Copyright (c) 2020 Jaroslav Kysela <perex@perex.cz>

import os
import sys
import re
from aconfig import AlsaConfig

SECTIONS = {
    'Linux Distribution': 'Distro',
    'DMI Information': 'Dmi',
    'ACPI Device Status Information': 'Acpi',
    'Kernel Information': 'Kernel',
    'ALSA Version': 'Version',
    'Loaded ALSA modules': 'Modules',
    'Sound Servers on this system': 'Servers',
    'Soundcards recognised by ALSA': 'Soundcards',
    'PCI Soundcards installed in the system': 'Pci',
    'Advanced information - PCI Vendor/Device/Subsystem ID\'s': 'Advanced',
    'Modprobe options (Sound related)': 'Modprobe',
    'Loaded sound module options': 'Modopts',
    'HDA-Intel Codec information': 'HdaCodec',
    'USB Mixer information': 'UsbMixer',
    'ALSA Device nodes': 'Devices',
    'ALSA configuration files': 'Configs',
    'Aplay/Arecord output': 'Aplay',
    'Amixer output': 'Amixer',
    'Alsactl output': 'Alsactl',
    'All Loaded Modules': 'AllModules',
    'Sysfs Files': 'Sysfs',
    'ALSA/HDA dmesg': 'Dmesg',
    'Packages installed': 'Packages'
}

class AlsaInfoError(Exception):
    """Indicates exceptions raised by alsainfo code."""

class AlsaInfoSoundcard:

    def __init__(self, card, parent=None):
        """The class with the soundcard information."""
        self.card = card
        self.parent = parent
        self.reset()

    def __repr__(self):
        return 'AlsaInfoSoundcard(id=%s, driver=%s, name=%s, longname=%s)' % \
                (repr(self.id), repr(self.driver), repr(self.name), repr(self.longname))

    def reset(self):
        self.id = ''
        self.driver = ''
        self.name = ''
        self.longname = ''
        self.mixername = ''
        self.components = ''
        self.module = None
        self.state = {}

    def getsys(self, path):
        if path == 'class/sound/card%s/device/driver/module' % self.card and self.module:
            return self.module

    def getCardIdByName(self, name):
        for c in self.parent.cards:
            card = self.parent.cards[c]
            if card.name == name:
                return card.id
        return ''

    def control_exists(self, ctl):
        base = self.state['control']
        for a in base:
            c = base[a]
            index = 'index' in c and c['index'] or 0
            if c['iface'] == ctl.iface and \
               c['name'] == ctl.name and \
               index == ctl.index:
                return True
        return False

class AlsaInfoDistro:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoDmesg:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoDmi:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoAcpi:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoKernel:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoVersion:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoModules:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoPackages:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoServers:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoSoundcards:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text
        lines = text.splitlines()
        r1 = r'[ ]*(?P<card>\w+)[ ]*\[(?P<id>.*)\]: (?P<driver>.*) - (?P<name>.*)[\n ]*(?P<longname>.*)'
        for i in range(0, len(lines), 2):
            if lines[i].strip() == '' or i + 2 > len(lines):
                continue
            t = lines[i+0] + '\n' + lines[i+1]
            m = re.match(r1, t)
            if m is None:
                raise AlsaInfoError("unable to decode soundcards")
            d = m.groupdict()
            card = int(d['card'])
            c = self.parent.card(card)
            for k in d:
                if k == 'card':
                    continue
                setattr(c, k, d[k].strip())

class AlsaInfoPci:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoAdvanced:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoModprobe:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoModopts:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text
        for m in text.split('!!Module:'):
            if not m: continue
            l = m.splitlines()
            mod = l[0].strip()
            if not mod: continue
            self.parent.modules.append(mod)

class AlsaInfoHdaCodec:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoUsbMixer:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoDevices:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoConfigs:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoAplay:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoAmixer:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text
        blocks = text.split('!!--')
        r1 = r".*--Mixer controls for card (?P<card>\w+) \[(?P<id>.*)\]\n\nCard hw:.*\n[ \t]*Mixer name[ \t]*: '(?P<mixername>.*)'\n[ \t]*Components[ \t]*: '(?P<components>.*)'\n"
        r2 = r".*--Mixer controls for card (?P<id>.*)\n\nCard hw:(?P<card>\w+).*\n[ \t]*Mixer name[ \t]*: '(?P<mixername>.*)'\n[ \t]*Components[ \t]*: '(?P<components>.*)'\n"
        for block in blocks:
            if not block:
                continue
            m = re.match(r1, block)
            if not m:
                m = re.match(r2, block)
            d = m.groupdict()
            card = int(d['card'])
            c = self.parent.card(card)
            for k in d:
                if k in ('card', 'id'):
                    continue
                setattr(c, k, d[k].strip())

class AlsaInfoAlsactl:

    def __init__(self, parent, text):
        self.parent = parent
        if text.startswith('--startcollapse--'):
            text = '\n'.join(text.splitlines()[1:-1])
        self.text = text
        cfg = AlsaConfig()
        cfg.loads(text)
        a = cfg.value()
        del cfg
        if not 'state' in a:
            raise AlsaInfoError('missing state compound')
        for k in a['state']:
            c = self.parent.card_by_id(k)
            c.state = a['state'][k]

class AlsaInfoAllModules:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfoSysfs:

    def __init__(self, parent, text):
        self.parent = parent
        self.text = text

class AlsaInfo:
    """Parses the output from the alsa-info.sh file."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.filename = None
        self.tree = {}
        self.cards = {}
        self.modules = []

    def card(self, card):
        if card in self.cards:
            return self.cards[card]
        c = AlsaInfoSoundcard(card, self)
        self.cards[card] = c
        return c

    def card_by_id(self, id):
        for card in self.cards:
            if self.cards[card].id == id:
                return self.cards[card]
        raise AlsaInfoError("unable to find card '%s'" % id)

    def load(self, filename):
        fp = open(filename)
        backlog = []
        section = ''
        while 1:
            line = fp.readline()
            if not line:
                break
            backlog.append(line)
            if line.startswith('!!--------'):
                if section:
                    cls = globals()['AlsaInfo' + section](self, ''.join(backlog[2:-2]).strip())
                    self.tree[section] = cls
                backlog = backlog[-2:]
                name = backlog[0][2:].strip()
                if not name in SECTIONS:
                    print(''.join(backlog))
                    raise AlsaInfoError("%s: unknown section %s" % (filename, repr(name)))
                section = SECTIONS[name]
        # a bit heuristic, should be improved
        for c in self.cards:
            if self.modules:
                self.cards[c].module = self.modules.pop(0)
