#! /usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later

# config.py - python bindings for the ALSA's configuration using ctype
# Copyright (c) 2020 Jaroslav Kysela <perex@perex.cz>

from ctypes import *

alsalib = CDLL('libasound.so')

class Test(Structure):
    pass

def deff(name, argtypes, restype):
    """define C function"""
    g = globals()
    g[name] = f = alsalib[name]
    f.argtypes = argtypes
    f.restype = restype

deff('snd_input_stdio_open', [c_void_p, c_char_p, c_char_p], c_int)
deff('snd_input_buffer_open', [c_void_p, c_char_p, c_ssize_t], c_int)
deff('snd_input_close', [c_void_p], c_int)
deff('snd_output_stdio_open', [c_void_p, c_char_p, c_char_p], c_int)
deff('snd_output_buffer_open', [c_void_p], c_int)
deff('snd_output_buffer_string', [c_void_p, c_void_p], c_size_t)
deff('snd_output_close', [c_void_p], c_int)
deff('snd_config_top', [c_void_p], c_int)
deff('snd_config_load', [c_void_p, c_void_p], c_int)
deff('snd_config_save', [c_void_p, c_void_p], c_int)
deff('snd_config_delete', [c_void_p], c_int)
deff('snd_config_iterator_first', [c_void_p], c_void_p)
deff('snd_config_iterator_next', [c_void_p], c_void_p)
deff('snd_config_iterator_end', [c_void_p], c_void_p)
deff('snd_config_iterator_entry', [c_void_p], c_void_p)
deff('snd_config_search', [c_void_p, c_char_p, c_void_p], c_int)
deff('snd_config_get_type', [c_void_p], c_int)
deff('snd_config_get_id', [c_void_p, c_void_p], c_int)
deff('snd_config_get_integer', [c_void_p, c_void_p], c_int)
deff('snd_config_get_integer64', [c_void_p, c_void_p], c_int)
deff('snd_config_get_real', [c_void_p, c_void_p], c_int)
deff('snd_config_get_string', [c_void_p, c_void_p], c_int)

SND_CONFIG_TYPE_INTEGER = 0
SND_CONFIG_TYPE_INTEGER64 = 1
SND_CONFIG_TYPE_REAL = 2
SND_CONFIG_TYPE_STRING = 3
SND_CONFIG_TYPE_POINTER = 4
SND_CONFIG_TYPE_COMPOUND = 1024

ALSACONFIG_TYPES = {
    SND_CONFIG_TYPE_INTEGER: 'integer',
    SND_CONFIG_TYPE_INTEGER64: 'integer64',
    SND_CONFIG_TYPE_REAL: 'real',
    SND_CONFIG_TYPE_STRING: 'string',
    SND_CONFIG_TYPE_POINTER: 'pointer',
    SND_CONFIG_TYPE_COMPOUND: 'compound'
}

class AlsaConfigError(Exception):
    """Indicates exceptions raised by a AlsaConfig class."""
    pass

class AlsaConfigIterator:

    def __init__(self, node):
        self.node = node
        self.next = None

    def __next__(self):
        if self.next is None:
            n = snd_config_iterator_first(self.node.config)
        else:
            n = self.next
        if n == snd_config_iterator_end(self.node.config):
            raise StopIteration
        n = c_void_p(n)
        e = snd_config_iterator_entry(n)
        self.next = snd_config_iterator_next(n)
        return AlsaConfig(self.node).loadp(c_void_p(e))

class AlsaConfig:

    def __init__(self, parent=None):
        self.parent = parent
        self.config = c_void_p()
        self.id = None
        self.type = None
        self.top = False

    def __del__(self):
        if self.top and self.config:
            snd_config_delete(self.config)

    def __iter__(self):
        if self.type == SND_CONFIG_TYPE_COMPOUND:
            return AlsaConfigIterator(self)
        raise AlsaConfigError("only compound nodes are iterable")

    def __getitem__(self, key):
        if self.type == SND_CONFIG_TYPE_COMPOUND:
            p = c_void_p()
            r = snd_config_search(self.config, key.encode('utf-8'), byref(p))
            if r < 0:
                raise AlsaConfigError("compound id '%s' not found" % key)
            c = AlsaConfig(self)
            c.loadp(p)
            return c
        raise AlsaConfigError("only compound nodes implements __contains__")

    def is_integer(self):
        return self.type == SND_CONFIG_TYPE_INTEGER

    def is_integer64(self):
        return self.type == SND_CONFIG_TYPE_INTEGER64

    def is_real(self):
        return self.type == SND_CONFIG_TYPE_REAL

    def is_string(self):
        return self.type == SND_CONFIG_TYPE_STRING

    def is_pointer(self):
        return self.type == SND_CONFIG_TYPE_STRING

    def is_compound(self):
        return self.type == SND_CONFIG_TYPE_COMPOUND

    def typename(self):
        if self.type in ALSACONFIG_TYPES:
            return ALSACONFIG_TYPES[self.type]
        return "type<%s>" % self.type

    def full_id(self):
        id = repr(self.id)
        parent = self.parent
        while not parent is None:
            if parent.id:
                id = repr(parent.id) + '.' + id
            parent = parent.parent
        return id

    def _load(self, input):
        config = c_void_p()
        if snd_config_top(byref(config)):
            snd_input_close(input)
            raise AlsaConfigError("unable to create top config")
        self.top = True
        self.loadp(config)
        self.type = SND_CONFIG_TYPE_COMPOUND
        if snd_config_load(config, input):
            raise AlsaConfigError("unable to load config")
        snd_input_close(input)

    def load(self, filename):
        """Load configuration from a file"""
        input = c_void_p()
        if snd_input_stdio_open(byref(input), filename.encode('utf-8'), b"r"):
            raise AlsaConfigError("unable to open filename: %s" % filename)
        return self._load(input)

    def loadp(self, config):
        """Load configuration node from C pointer"""
        if self.config:
            snd_config_delete(self.config)
        self.config = config
        self.type = snd_config_get_type(config)
        self.id = None
        id = c_char_p()
        if snd_config_get_id(config, byref(id)):
            raise AlsaConfigError("unable to get config id")
        if id.value:
            self.id = id.value.decode('utf-8')
        return self

    def loads(self, text):
        """Load configuration from a file"""
        input = c_void_p()
        buf = text.encode('utf-8');
        if snd_input_buffer_open(byref(input), buf, len(buf)):
            raise AlsaConfigError("unable to open text buffer")
        return self._load(input)

    def dumps(self):
        """Save (dump) configuration to a string"""
        output = c_void_p()
        if snd_output_buffer_open(byref(output)):
            raise AlsaConfigError("unable to create output buffer")
        if snd_config_save(self.config, output):
            snd_output_close(output)
            raise AlsaConfigError("unable to save configuration")
        buf = c_char_p()
        size = snd_output_buffer_string(output, byref(buf))
        res = size > 0 and buf.value[:size].decode('utf-8') or ''
        snd_output_close(output)
        return res

    def value(self):
        if not self.is_compound():
            if self.is_integer():
                val = c_int()
                if snd_config_get_integer(self.config, byref(val)):
                    raise AlsaConfigError("unable to get integer")
                return val.value
            if self.is_integer64():
                val = c_int64()
                if snd_config_get_integer(self.config, byref(val)):
                    raise AlsaConfigError("unable to get integer64")
                return val.value
            if self.is_real():
                val = c_double()
                if snd_config_get_integer(self.config, byref(val)):
                    raise AlsaConfigError("unable to get real")
                return val.value
            if self.is_string():
                val = c_char_p()
                if snd_config_get_string(self.config, byref(val)):
                    raise AlsaConfigError("unable to get string")
                return val.value.decode('utf-8')
            if self.is_pointer():
                raise AlsaConfigError("cannot handle pointer type")
        else:
            x = 0
            a = True
            for node in self:
                if node.id != str(x):
                    a = False
                    break
                x += 1
            if a:
                d = []
                for node in self:
                    d.append(node.value())
            else:
                d = {}
                for node in self:
                    d[node.id] = node.value()
            return d                

if __name__ == '__main__':

    c = AlsaConfig()
    c.load('../../ucm2/sof-hda-dsp/sof-hda-dsp.conf')
    print(c.dumps(), end='')
    c.loads('a { b 1 c [ "first" "second" ] }')
    print(c.dumps(), end='')
    from pprint import pprint
    pprint(c.value())
