#! /usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later

# config.py - python bindings for the ALSA's configuration using ctype
# Copyright (c) 2020 Jaroslav Kysela <perex@perex.cz>

from ctypes import *
from errno import errorcode, ENOENT

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
deff('snd_config_remove', [c_void_p], c_int)
deff('snd_config_copy', [c_void_p, c_void_p], c_int)
deff('snd_config_add', [c_void_p, c_void_p], c_int)
deff('snd_config_add_after', [c_void_p, c_void_p], c_int)
deff('snd_config_add_before', [c_void_p, c_void_p], c_int)
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
deff('snd_config_set_id', [c_void_p, c_char_p], c_int)

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

class AlsaConfigBase:

    def type_compare(self, node):
        return self.type == node.type

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
        
    def is_array(self):
        if self.type != SND_CONFIG_TYPE_COMPOUND:
            return False
        x = 0
        a = True
        for node in self:
            if node.id != str(x):
               a = False
               break
            x += 1
        return a

    def is_empty(self):
        return len(self) == 0

    def keys(self):
        if self.type != SND_CONFIG_TYPE_COMPOUND:
            return False
        r = []
        for n in self:
            r.append(n.id)
        return r

    def full_id(self):
        id = repr(self.id)
        parent = self.parent
        while not parent is None:
            if parent.id:
                id = repr(parent.id) + '.' + id
            parent = parent.parent
        return id

    def typename(self):
        if self.type in ALSACONFIG_TYPES:
            return ALSACONFIG_TYPES[self.type]
        return "type<%s>" % self.type

    def split_id(self, id):
        r = []
        id1 = id
        while id1:
            if id1[0] in ('"', "'"):
                d = id1[0]
                id = id1[1:]
                p = id1.find(id1, d)
                if p < 0:
                    raise AlsaConfigError("wrong id %s" % repr(id))
                r.append(id1[:p])
                id1 = id1[1:]
                if id1 and not id1['.']:
                    raise AlsaConfigError("wrong id %s" % repr(id))
                id1 = id1[1:]
            else:
                r.append(id1)
                break
        return r

    def search(self, id):
        """Search (complex / dot separated) id in the tree"""
        a = self.split_id(id)
        parent = self
        for k in a:
            if not k in parent:
                return None
            parent = parent[k]
        return parent

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

class AlsaConfig(AlsaConfigBase):

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

    def __contains__(self, node):
        id = node
        if type(node) != type(''):
            id = node.id
        p = c_void_p()
        r = snd_config_search(self.config, id.encode('utf-8'), byref(p))
        return r == 0

    def __getitem__(self, key):
        if self.type == SND_CONFIG_TYPE_COMPOUND:
            p = c_void_p()
            r = snd_config_search(self.config, key.encode('utf-8'), byref(p))
            if r < 0:
                raise AlsaConfigError("compound id '%s' not found" % key)
            c = AlsaConfig(self)
            c.loadp(p)
            return c
        raise AlsaConfigError("only compound nodes implements __getitem__")

    def __len__(self):
        if not self.is_compound():
            raise AlsaConfigError("node %s is not a compound" % self.full_id())
        r = 0
        n = snd_config_iterator_first(self.config)
        while n != snd_config_iterator_end(self.config):
            n = snd_config_iterator_next(n)
            r += 1
        return r

    def set_id(self, id):
        """Set new id string"""
        if snd_config_set_id(self.config, str(id).encode('utf-8')):
            raise AlsaConfigError("unable to set new id")
        self.id = str(id)

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
        """Load configuration from a string"""
        input = c_void_p()
        buf = text.encode('utf-8');
        if snd_input_buffer_open(byref(input), buf, len(buf)):
            raise AlsaConfigError("unable to open text buffer")
        return self._load(input)

    def copy(self):
        """Create a new duplicate value"""
        c = AlsaConfig()
        if snd_config_copy(byref(c.config), self.config):
            raise AlsaConfigError("unable to copy configuration node")
        return c

    def remove(self):
        """Remove this node from the parent"""
        if snd_config_remove(self.config):
            raise AlsaConfigError("unable to remove node")
        self.parent = None

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
            if self.is_array():
                d = []
                for node in self:
                    d.append(node.value())
            else:
                d = {}
                for node in self:
                    d[node.id] = node.value()
            return d                

    def add(self, node):
        r = snd_config_add(self.config, node.config)
        if r:
            raise AlsaConfigError("cannot add node %s to parent node %s [%s]" % (repr(node.id), repr(self.id), errorcode[-r]))
        node.parent = self.parent

    def add_before(self, node):
        r = snd_config_add_before(self.config, node.config)
        if r:
            raise AlsaConfigError("cannot add node %s before node %s [%s]" % (repr(node.id), repr(self.id), errorcode[-r]))
        node.parent = self.parent

    def add_after(self, node):
        r = snd_config_add_after(self.config, node.config)
        if r:
            raise AlsaConfigError("cannot add node %s after node %s [%s]" % (repr(node.id), repr(self.id), errorcode[-r]))
        node.parent = self.parent

class AlsaConfigTreeIterator:

    def __init__(self, node):
        self.node = node
        self.next = None

    def __next__(self):
        n = self.next
        if n is None:
            if len(self.node.val) == 0:
                raise StopIteration
            n = self.node.val[0]
        if n == -1:
            raise StopIteration
        idx = self.node.val.index(n)
        if len(self.node.val) > idx + 1:
            self.next = self.node.val[idx + 1]
        else:
            self.next = -1
        return n

class AlsaConfigTree(AlsaConfigBase):
    """This is fully cached configuration tree which may be extended."""

    def __init__(self, parent=None):
        self.parent = parent
        self.id = None
        self.type = None
        self.val = None
        self.top = False

    def __iter__(self):
        if self.type == SND_CONFIG_TYPE_COMPOUND:
            return AlsaConfigTreeIterator(self)
        raise AlsaConfigError("only compound nodes are iterable")

    def __contains__(self, node):
        if self.type != SND_CONFIG_TYPE_COMPOUND:
            raise AlsaConfigError("only compound nodes implement __contains__")
        id = node
        if type(node) != type(''):
            id = node.id
        for v in self.val:
            if v.id == id:
                return True
        return False

    def __getitem__(self, key):
        if self.type == SND_CONFIG_TYPE_COMPOUND:
            for n in self.val:
                if n.id == key:
                    return n
            raise AlsaConfigError("compound id '%s' not found" % key)
        raise AlsaConfigError("only compound nodes implements __getitem__")

    def __len__(self):
        if not self.is_compound():
            raise AlsaConfigError("node %s is not a compound" % self.full_id())
        return len(self.val)

    def set_id(self, id):
        """Set new id string"""
        id = str(id)
        if self.id == id:
            return
        if self.parent:
            for n in self.parent.val:
                if n.id == id:
                    raise AlsaConfigError("parent %s has already identical identifier %s" % (self.full_id(), id))
        self.id = id

    def _load(self, c):

        def val(t, o):
            t.id = o.id
            t.type = o.type
            if not o.is_compound():
                t.val = o.value()
            else:
                t.val = []
                for n in o:
                    ac = self.__class__(t)
                    t.val.append(ac)
                    val(ac, n)

        self.top = True
        val(self, c)

    def load(self, filename):
        """Load configuration from a file"""
        c = AlsaConfig()
        c.load(filename)
        return self._load(c)

    def loads(self, text):
        """Load configuration from a string"""
        c = AlsaConfig()
        c.loads(text)
        return self._load(c)

    def copy(self):
        """Create a new duplicate value"""

        def one(dst, src):
            dst.id = src.id
            dst.type = src.type
            dst.top = src.top
            if not dst.is_compound():
                dst.val = src.val
            else:
                dst.val = []
                for src2 in src:
                    dst2 = self.__class__(dst)
                    dst.val.append(dst2)
                    one(dst2, src2)
                    dst2.post()

        c = self.__class__()
        one(c, self)
        return c

    def remove(self):
        """Remove this node from the parent"""
        if self.parent is None:
            raise AlsaConfigError("node %s has not a parent" % self.full_id())
        self.parent.val.remove(self)
        self.parent = None

    def dumps(self):
        """Save (dump) configuration to a string"""

        def one(n):
            if n.is_compound():
                r = ''
                for n2 in n:
                    r += one(n2)
            else:
                r = '%s %s\n' % (n.full_id(), repr(n.value()))
            return r

        r = one(self)
        return r

    def value(self):
        
        if not self.is_compound():
            return self.val
        else:
            if self.is_array():
                d = []
                for node in self:
                    d.append(node.value())
            else:
                d = {}
                for node in self:
                    d[node.id] = node.value()
            return d                

    def add(self, node):
        if not self.is_compound():
            raise AlsaConfigError("node %s is not a compound" % self.full_id())
        node.parent = self
        self.val.append(node)

    def add_before(self, node):
        if self.parent is None:
            raise AlsaConfigError("node %s has not a parent" % self.full_id())
        idx = self.parent.val.index(self)
        self.parent.val.insert(idx, node)
        node.parent = self.parent

    def add_after(self, node):
        if self.parent is None:
            raise AlsaConfigError("node %s has not a parent" % self.full_id())
        idx = self.parent.val.index(self)
        self.parent.val.insert(idx + 1, node)
        node.parent = self.parent

if __name__ == '__main__':

    c = AlsaConfig()
    c.load('../../ucm2/sof-hda-dsp/sof-hda-dsp.conf')
    print(c.dumps(), end='')
    c.loads('a { b 1 c [ "first" "second" ] }')
    print(c.dumps(), end='')
    from pprint import pprint
    pprint(c.value())
