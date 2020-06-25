#! /usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later

# alsajson.py - ALSA dummy alsa-info.sh json emulator
# Copyright (c) 2020 Jaroslav Kysela <perex@perex.cz>

import os
import sys
import json
from ucmlib import AlsaControl

VALID_JSON_FIELDS = [
    'comment', 'id', 'driver', 'name', 'longname', 'mixername', 'module', 'components'
]

class AlsaJsonError(Exception):
    """Indicates exceptions raised by alsa json code."""

class AlsaJsonSoundcard:

    def __init__(self, json_id, card):
        """The class with the soundcard information."""
        self.json_id = json_id
        self.card = card
        self.reset()

    def __repr__(self):
        return 'AlsaJsonSoundcard(json=%s, id=%s, driver=%s, name=%s, longname=%s)' % \
                (repr(self.json_id), repr(self.id), repr(self.driver), repr(self.name), repr(self.longname))

    def reset(self):
        self.id = ''
        self.driver = ''
        self.name = ''
        self.longname = ''
        self.mixername = ''
        self.components = ''
        self.module = ''
        self.controls = []
        self.linked = {}

    def getsys(self, path):
        if path == 'class/sound/card%s/device/driver' % self.card and self.module:
            return self.module

    def getCardIdByName(self, name):
        if name in self.linked:
            return self.linked[name]
        return ''

    def control_exists(self, ctl):
        for c in self.controls:
            if c.match(ctl):
                return True
        return False

    def load_control(self, control):
        for c in control:
            ctl = AlsaControl()
            ctl.parse(c['id'])
            self.controls.append(ctl)

    def load_linked(self, linked):
        for l in linked:
            self.linked[l] = linked[l]

    def load(self, config):
        for f in config:
            if f == 'comment':
                continue
            if f == 'control':
                self.load_control(config[f])
                continue
            if f == 'linked':
                self.load_linked(config[f])
                continue
            if not f in VALID_JSON_FIELDS:
                raise AlsaJsonError("field '%s' is not valid" % f)
            setattr(self, f, config[f])

class AlsaJson:
    """Parses the dummy json configuration."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.filename = None
        self.cards = {}

    def card(self, card):
        if card in self.cards:
            return self.cards[card]
        c = AlsaInfoSoundcard(card)
        self.cards[card] = c
        return c

    def card_by_id(self, id):
        for card in self.cards:
            if self.cards[card].id == id:
                return self.cards[card]
        raise AlsaInfoError("unable to find card '%s'" % id)

    def load(self, filename):
        self.reset()
        self.filename = filename
        fp = open(filename)
        if filename.endswith('.py'):
            ctx = fp.read(128 * 1024)
            glob = {}
            exec(compile(ctx, filename, 'exec'), glob)
            topdir = os.path.abspath(filename + '/../..')
            self.json = glob['generate_json'](topdir)
        else:
            self.json = json.load(fp)
        fp.close()
        index = 0
        for c in self.json:
             card = AlsaJsonSoundcard(c, index)
             card.load(self.json[c])
             self.cards[index] = card
             index += 1
