#! /usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later

# alsajson.py - ALSA dummy alsa-info.sh json emulator
# Copyright (c) 2020 Jaroslav Kysela <perex@perex.cz>

import os
import sys
import json
from ucmlib import AlsaControl

VALID_JSON_FIELDS = [
    'comment', 'id', 'driver', 'name', 'longname', 'mixername', 'components'
]

class AlsaJsonError(Exception):
    """Indicates exceptions raised by alsa json code."""

class AlsaJsonSoundcard:

    def __init__(self, card):
        """The class with the soundcard information."""
        self.card = card
        self.reset()

    def reset(self):
        self.id = ''
        self.driver = ''
        self.name = ''
        self.longname = ''
        self.mixername = ''
        self.components = ''
        self.controls = []

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

    def load(self, config):
        for f in config:
            if f == 'comment':
                continue
            if f == 'control':
                self.load_control(config[f])
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
        self.json = json.load(fp)
        fp.close()
        index = 0
        for c in self.json:
             card = AlsaJsonSoundcard(index)
             card.load(self.json[c])
             self.cards[index] = card
             index += 1
