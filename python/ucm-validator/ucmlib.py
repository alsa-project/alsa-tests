#! /usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later

# ucmlib.py - ALSA Use Case Manager routines
# Copyright (c) 2020 Jaroslav Kysela <perex@perex.cz>

import os
import sys
import re
import types
from aconfig import AlsaConfigTree

VALID_ID_LISTS = {
    'top': {
        'Syntax': 'integer',
        'UseCasePath': 'compound',
        'LibraryConfig': 'compound',
    },
    'UseCasePath': {
        'Version': 'integer',
        'Directory': 'string',
        'File': 'string'
    },
    'master': {
        'Syntax': 'integer',
        'Comment': 'string',
        'SectionDefaults': 'compound',
        'SectionUseCase': 'compound',
        'FixedBootSequence': 'compound',
        'BootSequence': 'compound',
        'ValueDefaults': 'compound',
        'LibraryConfig': 'compound',
        'Error': 'string',
    },
    'Include': {
        'File': 'string',
        'After': 'compoundstring',
        'Before': 'compoundstring'
    },
    'If': {
        'Condition': 'compound',
        'True': 'compound',
        'False': 'compound',
        'After': 'compoundstring',
        'Before': 'compoundstring'
    },
    'DefineRegex': {
        'String': 'string',
        'Regex': 'string',
        'Flags': 'string'
    },
    'ConditionControlExists': {
        'Type': 'string',
        'Control': 'string',
        'ControlEnum': 'string'
    },
    'ConditionString': {
        'Type': 'string',
        'String1': 'string',
        'String2': 'string',
        'Haystack': 'string',
        'Needle': 'string',
        'Empty': 'string'
    },
    'ConditionRegexMatch': {
        'Type': 'string',
        'Regex': 'string',
        'String': 'string'
    },
    'SectionUseCase': {
        'File': 'string',
        'Comment': 'string'
    },
    'UseCaseFile': {
        'SectionVerb': 'compound',
        'SectionDevice': 'compound',
        'RenameDevice': 'compound',
        'RemoveDevice': 'compound',
        'LibraryConfig': 'compound'
    },
    'SectionVerb': {
        'Value': 'compound',
        'EnableSequence': 'compound',
        'DisableSequence': 'compound'
    },
    'SectionDevice': {
        'Comment': 'string',
        'EnableSequence': 'compound',
        'DisableSequence': 'compound',
        'ConflictingDevice': 'compound',
        'SupportedDevice': 'compound',
        'Value': 'compound'
    },
    'Value': {
        'TQ': 'string',
        'PlaybackPriority': 'intstring',
        'PlaybackChannels': 'intstring',
        'PlaybackPCM': 'string',
        'PlaybackMixerElem': 'string',
        'PlaybackMasterElem': 'string',
        'PlaybackVolume': 'string',
        'PlaybackSwitch': 'string',
        'CapturePriority': 'intstring',
        'CaptureChannels': 'intstring',
        'CapturePCM': 'string',
        'CaptureMixerElem': 'string',
        'CaptureMasterElem': 'string',
        'CaptureVolume': 'string',
        'CaptureSwitch': 'string',
        'JackControl': 'string',
        'JackHWMute': 'string',
        'JackCTL': 'string',
        'JackDev': 'string',
        'MinBufferLevel': 'intstring',
    }
}

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
    'USB'
}

def dict_array_append(d, key, val):
    if not key in d:
        d[key] = []
    d[key].append(val)

class AlsaConfigUcm(AlsaConfigTree):
    """Class to trace origin"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.origin = None
        self.prefix = None

    def origin_id(self):
        return self.origin

    def _load(self, c):

        def one(n):
            n.origin = self.prefix + n.full_id()
            if n.is_compound():
                for n2 in n:
                    one(n2)

        super()._load(c)
        one(self)

    def load(self, filename, origin=None):
        self.prefix = ''
        if origin:
            self.prefix = origin
        super().load(filename)

class AlsaControlError(Exception):
    """Indicates exceptions raised by AlsaControl class."""

class AlsaControl:
    """Basic ALSA Control abstraction."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.iface = None
        self.name = None
        self.index = None
        self.type = None

    def match(self, other):
        if self.iface == other.iface and \
           self.name == other.name and \
           self.index == other.index:
            return True
        return False

    def parse(self, s):
        r1 = r"(?:([^=]+)='([^']+)'(?:,|$)+)|(?:([^=]+)=\"([^\"]+)\"(?:,|$)+)|(?:([^=]+)=([^=]+)(?:,|$)+)"
        self.iface = 'MIXER'
        self.index = 0
        for m in re.findall(r1, s):
            field = (m[0] or m[2]) or m[4]
            value = (m[1] or m[3]) or m[5]
            field = field.strip()
            value = value.strip()
            if not field in ('iface', 'name', 'index'):
                raise AlsaControlError("wrong identifier '%s' (%s)" % (field, s))
            setattr(self, field, value)

class UcmError(Exception):
    """Indicates exceptions raised by ucm."""

class UcmValue:

    def __init__(self, parent):
        self.parent = parent
        self.reset()

    def log(self, lvl, msg, *args):
        self.parent.log(lvl, msg, *args)

    def error(self, node, msg, *args):
        self.parent.error(node, msg, *args)

    def warning(self, node, msg, *args):
        self.parent.warning(node, msg, *args)

    def reset(self):
        self.values = {}

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, key):
        return self.values[key]

    def shortfn(self):
        return self.parent.shortfn()

    def validate(self, what, node, prefix='', extra=None):
        return self.parent.validate(what, node, extra=extra)

    def substitute(self, node):
        return self.parent.substitute(0, node, self)

    def load_value(self, value_node, vextra=None):
        self.parent.evaluate_inplace(value_node)
        for node in value_node:
            id = self.validate('Value', node, extra=vextra)
            self.substitute(node) # only for test
            self.values[id] = node.value()

class UcmDevice:

    def __init__(self, verb):
        self.verb = verb
        self.ucm = verb.ucm
        self.reset()

    def log(self, lvl, msg, *args):
        self.ucm.log(lvl, msg, *args)

    def error(self, node, msg, *args):
        self.verb.error(node, "Device=%s %s" % (self.name, msg), *args)

    def warning(self, node, msg, *args):
        self.verb.warning(node, "Device=%s %s" % (self.name, msg), *args)

    def reset(self):
        self.name = None
        self.comment = None
        self.conflicting = None
        self.supported = None
        self.enable = None
        self.disable = None
        self.values = None

    def validate(self, what, node, prefix='', extra=None):
        prefix = "%s(Device=%s) " % (prefix, self.name)
        return self.verb.validate(what, node, prefix, extra=extra)

    def substitute(self, syntax, node, origin=None):
        return self.verb.substitute(syntax, node, origin and origin or self)

    def substitute2(self, syntax, node, s, origin=None):
        return self.verb.substitute2(syntax, node, s, origin and origin or self)

    def shortfn(self):
        return self.verb.shortfn()

    def getval(self, name):
        if self.values and name in self.values:
            return self.values[name]
        return self.verb.getval(name)

    def getintval(self, name):
        v = self.getval(name)
        return v is None and None or int(v)

    def getsval(self, name):
        v = self.getval(name)
        if v is None:
            return None
        return self.substitute2(2, None, v)

    def getsintval(self, name):
        v = self.getsval(name)
        if v is None:
            return None
        return int(v)

    def evaluate_inplace(self, if_node, origin=None):
        return self.ucm.evaluate_inplace(if_node, origin and origin or self)

    def load_array(self, array_node):
        return self.verb.load_array(array_node)

    def load_device_list(self, dlist_node):
        return self.verb.load_device_list(dlist_node)

    def load_sequence(self, array_node):
        return self.verb.load_sequence(array_node)

    def load_device(self, device_node):
        name = self.substitute2(3, device_node, device_node.id)
        self.log(1, "Device '%s'", name)
        self.reset()
        self.name = name
        add = []
        self.ucm.evaluate_inplace(device_node, self)
        for node in device_node:
            id = self.validate('SectionDevice', node)
            if id == 'Comment':
                self.comment = node.value()
            elif id == 'EnableSequence':
                self.enable = self.load_sequence(node)
            elif id == 'DisableSequence':
                self.disable = self.load_sequence(node)
            elif id == 'ConflictingDevice':
                self.conflicting = self.load_device_list(node)
            elif id == 'SupportedDevice':
                self.supported = self.load_device_list(node)
            elif id == 'Value':
                self.values = UcmValue(self)
                self.values.load_value(node)

    def get_pcm(self, stream):
        name = stream + 'PCM'
        if not self.getval(name):
            return None
        d = {}
        d['prio'] = self.getsintval(stream + 'Priority')
        return d

    def check_pcm_name(self, name):
        oname = name
        r2 = r"^(plug|)hw:\${CardId},0$"
        m2 = re.match(r2, name)
        if m2:
            self.warning(0, 'PCM name %s can be trucated (remove trailing zero /,0/)' % repr(name))
        r1 = r"^(plug|)hw:([\${}:a-zA-Z0-9_-]+)(,[0-9]+|)$"
        m1 = re.match(r1, name)
        if m1:
            return
        r1 = r"^(plug|)hw:[\$]{1,2}\{.*\}(,[0-9]+|)$"
        m1 = re.match(r1, name)
        if m1:
            return
        self.error(0, 'PCM name %s is invalid' % repr(name))

    def check_pcm(self):
        count = 0
        for prefix in ('Playback', 'Capture'):
            name = prefix + 'PCM'
            pcm = self.getval(name)
            if pcm:
                count += 1
                if self.verb.getval(name) and self.verb.value_count(name) > 1:
                    if self.ucm.getval(name):
                        self.error(0, '%s defined in ValueDefaults' % name)
                    else:
                        self.error(0, '%s defined in SectionVerb' % name)
                self.check_pcm_name(pcm)
                pname = prefix + 'Priority'
                v = self.getsintval(pname)
                if v is None:
                    self.error(0, '%s not defined' % pname)
                if type(v) == type(''):
                    self.warning(0, '%s is not an integer' % pname)
                cname = prefix + 'Channels'
                v = self.getsintval(cname)
                if type(v) == type(''):
                    self.warning(0, '%s is not an integer' % cname)
                if v == 2:
                    self.warning(0, '%s is 2 which is the application default' % cname)
        if count == 0:
            self.error(0, 'device %s has no PCM defined!' % repr(self.name))

    def check_device_list(self, what, devices):
        if devices is None:
            return
        for d in devices:
            if not d in self.verb.devices:
                self.error(0, "%s device '%s' is not valid" % (what, d))

    def check(self):
        self.check_pcm()
        self.check_device_list('ConflictingDevices', self.conflicting)
        self.check_device_list('SupportedDevices', self.supported)

    def dump_device_list(self, what, devices):
        r = ''
        if devices:
            for idx in range(len(devices)):
                r += '%s.%s = %s' % (what, idx, devices[idx])
        return r

    def dump(self):
        r = 'Device: "%s"\n' % self.name
        v = self.dump_device_list('ConflictingDevices', self.conflicting)
        if v:
            r += '\n'.join(map(lambda x: '  ' + x, v.splitlines())) + '\n'
        v = self.dump_device_list('SupportedDevices', self.supported)
        if v:
            r += '\n'.join(map(lambda x: '  ' + x, v.splitlines())) + '\n'
        for v in self.values:
            r += '  Value.%s = %s\n' % (v, repr(self.values[v]))
        return r

class UcmVerb:

    def __init__(self, ucm):
        self.ucm = ucm
        self.reset()

    def log(self, lvl, msg, *args):
        self.ucm.log(lvl, msg, *args)

    def error(self, node, msg, *args):
        self.ucm.error(node, "Verb=%s %s" % (self.name, msg), *args)

    def warning(self, node, msg, *args):
        self.ucm.warning(node, "Verb=%s %s" % (self.name, msg), *args)

    def reset(self):
        self.filename = None
        self.name = None
        self.comment = None
        self.values = None
        self.enable = []
        self.disable = []
        self.boot = []
        self.devices = {}

    def validate(self, what, node, prefix='', extra=None):
        prefix = "%s(Verb=%s) " % (prefix, self.name)
        return self.ucm.validate(what, node, prefix, extra=extra)

    def substitute(self, syntax, node, origin=None):
        return self.ucm.substitute(syntax, node, origin and origin or self)

    def substitute2(self, syntax, node, s, origin=None):
        return self.ucm.substitute2(syntax, node, s, origin and origin or self)

    def shortfn(self):
        return self.ucm.shortfn() + '@' + self.filename

    def getval(self, name):
        if self.values and name in self.values:
            return self.values[name]
        return self.ucm.getval(name)

    def value_count(self, pcm):
        count = 0
        for device in self.devices:
            if self.devices[device].getval(pcm):
                count += 1
        return count

    def evaluate_inplace(self, if_node, origin=None):
        return self.ucm.evaluate_inplace(if_node, origin and origin or self)

    def load_array(self, array_node):
        return self.ucm.load_array(array_node, self)

    def load_device_list(self, dlist_node):
        return self.ucm.load_device_list(dlist_node, self)

    def load_sequence(self, array_node):
        return self.ucm.load_sequence(array_node, self)

    def section_verb(self, verb_node):
        self.evaluate_inplace(verb_node)
        for node in verb_node:
            id = self.validate('SectionVerb', node)
            if id == 'EnableSequence':
                self.enable = self.load_sequence(node)
            elif id == 'DisableSequence':
                self.disable = self.load_sequence(node)
            elif id == 'Value':
                self.values = UcmValue(self)
                self.values.load_value(node)

    def list_rename(self, what, l, src, dst):
        if not l:
            return
        if src in l:
            if dst in l:
                self.error(0, 'RenameDevices %s target device %s already in list' % (what, dst))
            l.remove(src)
            l.append(dst)

    def list_remove(self, what, l, src):
        if not l:
            return
        if src in l:
            l.remove(src)

    def load_verb(self, verbname, filename):
        self.reset()
        self.name = verbname
        self.filename = filename
        if filename[0] != '/':
            filename = self.ucm.cfgdir() + '/' + filename
        else:
            filename = self.ucm.topdir() + '/' + filename[1:]
        self.ucm.indent_check(filename)
        aconfig = AlsaConfigUcm()
        self.log(1, "Verb '%s', file '%s'", verbname, self.ucm.shortfn(filename))
        aconfig.load(filename)
        rename_dict = {}
        remove_list = {}
        self.evaluate_inplace(aconfig)
        for node in aconfig:
            id = self.validate('UseCaseFile', node)
            if id == 'SectionVerb':
                self.section_verb(node)
            elif id == 'SectionDevice':
                for node2 in node:
                    dev = UcmDevice(self)
                    dev.load_device(node2)
                    self.devices[dev.name] = dev
            elif id == 'RenameDevice':
                rename_dict = node.value()
            elif id == 'RemoveDevice':
                remove_list = node.value()
        if not self.ucm.verify:
            return
        for src in rename_dict:
            dst = rename_dict[src]
            if dst in self.devices:
                self.error(0, 'RenameDevice - %s already defined' % repr(dst))
            elif not src in self.devices:
                self.error(0, 'RenameDevice - %s does not exist' % repr(src))
            self.devices[dst] = self.devices[src]
            self.devices[dst].name = dst
            del self.devices[src]
            for dev in self.devices.values():
                self.list_rename('ConflictingDevices', dev.conflicting, src, dst)
                self.list_rename('SupportedDevices', dev.supported, src, dst)
        for src in remove_list:
            if src in self.devices:
                self.error(0, 'RemoveDevice - %s is defined!' % repr(src))
            for dev in self.devices.values():
                self.list_remove('ConflictingDevices', dev.conflicting, src)
                self.list_remove('SupportedDevices', dev.supported, src)

    def check_device_names(self):
        """Check if UCM device names are valid for the verb."""
        names = list(self.devices.keys())
        names.sort()
        r1 = r"(?P<base>[a-zA-Z]+)[ ]{0,1}(?P<index>[0-9]*)"
        prev = {}
        for name in names:
            m = re.match(r1, name)
            d = m.groupdict(m)
            if not d['base'] in VALID_DEVICE_NAMES:
                self.error(0, 'device name "%s" unknown (see the specification)' % name)
            if d['base'] + d['index'] != name and \
               d['base'] + ' ' + d['index'] != name:
                self.error(0, 'device name "%s" is not valid (%s[ %s])' % (name, d['base'], d['index']))
            index = None
            if prev and prev['base'] == d['base']:
                if d['index']:
                    index = int(d['index'])
                    if prev and index > 1:
                        if prev['index'] + 1 != index:
                            self.error(0, 'non-continous device index (device "%s" previous "%s")' % (name, prev['name']))
                else:
                    self.error(0, 'mixing non-indexed devices with indexed devices is not allowed (device "%s" previous "%s")' % (name, prev['name']))
            else:
                if d['index']:
                    index = int(d['index'])
            prev = {'name': name, 'base': d['base'], 'index': index}

    def check_priorities(self):
        # priorities
        d = {'Playback': {}, 'Capture': {}}
        for s in d:
            d[s]['prio'] = {}
        for device in self.devices:
            dev = self.devices[device]
            for stream in ('Playback', 'Capture'):
                pcm = dev.get_pcm(stream)
                if pcm:
                    dict_array_append(d[stream]['prio'], pcm['prio'], dev)
        for s in d:
            for p in d[s]['prio']:
                prio = d[s]['prio'][p]
                if len(prio) > 1:
                    names = tuple(map(lambda dev: dev.name, prio))
                    self.error(0, 'duplicate %sPriority %s devices %s' % (s, p, repr(names)))

    def check_jackhwmute(self):
        for device in self.devices:
            dev = self.devices[device]
            hwmute = dev.getval('JackHWMute')
            if not hwmute:
                continue
            if not hwmute in self.devices:
                self.error(0, 'Device %s JackHWMute device name %s unknown' % (repr(device), repr(hwmute)))
            if not dev.getval('JackControl'):
                self.error(0, 'Device %s JackControl is not defined (JackHWMute)' % repr(device))

    def check(self):
        self.check_device_names()
        for device in self.devices:
            self.devices[device].check()
        self.check_priorities()
        self.check_jackhwmute()

    def dump(self):
        r = 'Verb: "%s"\n' % self.name
        r += '  File: %s\n' % self.filename
        for device in self.devices:
            v = self.devices[device].dump()
            if v:
                r += '\n'.join(map(lambda x: '  ' + x, v.splitlines())) + '\n'
        return r

class Ucm:

    def __init__(self, verify=None):
        """Ucm configuration class."""
        self.verify = verify
        self.var = {}

    def id(self):
        return self.shortfn(self.filename)

    def log(self, lvl, msg, *args):
        """Write a log message (override)."""
        pass

    def error(self, node, msg, *args):
        if not node is None and node != 0:
            raise UcmError("%s: %s %s" % (self.id(), node.full_id(), msg % args))
        else:
            raise UcmError("%s: %s" % (self.id(), msg % args))

    def warn(self, msg, *args):
        """Write a warning message (override)."""
        pass

    def warning(self, node, msg, *args):
        if not node is None and node != 0:
            self.warn("%s: %s %s", self.id(), node.full_id(), msg % args)
        else:
            self.warn("%s: %s", self.id(), msg % args)

    def reset(self):
        self.syntax = 0
        self.comment = None
        self.verbs = []
        self.values = None
        self.filename = ''

    def cfgdir(self):
        return os.path.split(self.filename)[0]

    def topdir(self):
        d = self.cfgdir()
        for x in range(2):
            d = os.path.split(d)[0]
            if os.path.exists('%s/ucm.conf' % d):
                return d
        raise UcmError("unable to determine top directory (%s)!" % self.cfgdir())

    def shortfn(self, filename=None):
        if filename is None:
            filename = self.filename
        topdir = self.topdir()
        if not filename.startswith(topdir):
            raise UcmError("shortfn mismatch '%s' / '%s'" % (topdir, filename))
        return filename[len(topdir)+1:]

    def get_id(self, node):
        if not self.verify and node.id.find('#') >= 0:
            id, id2 = node.id.split('#')
        else:
            id = node.id
        return id

    def validate(self, what, node, prefix='', extra=None):
        if not what in VALID_ID_LISTS:
            raise UcmError("%sdefine validity list for '%s'" % (prefix, what))
        vlist = VALID_ID_LISTS[what]
        id = self.get_id(node)
        if not id in vlist:
            if not extra or not id in extra:
                self.error(node, "%sfield is not known for '%s'" % (prefix, what))
            else:
                vlist = extra
        t = vlist[id]
        t2 = node.typename()
        if t == 'intstring':
            if t2 == 'string':
                try:
                    val = int(self.substitute(2, node))
                except:
                    self.error(node, "%svalue %s cannot be converted to integer" % (prefix, repr(node.value())))
                return id
            t = 'integer'
        if t == 'compoundstring':
            if not node.is_compound():
                self.error(node, "%sis not type compound (has type '%s')" % (prefix, node.typename()))
            for x in node:
                if not x.is_string():
                    self.error(x, "%sis not type string (has type '%s')" % (prefix, x.typename()))
            return id
        if t != node.typename():
            self.error(node, "%sis not type %s (has type '%s')" % (prefix, repr(t), node.typename()))
        return id

    def getval(self, name):
        if self.values and name in self.values:
            return self.values[name]
        return None

    def load_array(self, array_node, origin=None):
        if not array_node.is_array():
            self.error(array_node, "is not array")
        v = array_node.value()
        if len(v) == 0:
            self.error(array_node, "is empty")
        return v

    def load_device_list(self, dlist_node, origin=None):
        if not dlist_node.is_array():
            self.error(dlist_node, "is not array")
        r = []
        for v in dlist_node.value():
            v = self.substitute2(3, dlist_node, v, origin)
            r.append(v)
        return r

    def load_sequence(self, array_node, origin=None):
        v = self.load_array(array_node)
        for idx in range(0, len(v), 2):
            cmd, arg = v[idx], v[idx + 1]
            if cmd == 'cdev' and arg.find('CardId') >= 0:
                self.error(array_node, "cdev is aready set in alsa-lib")
            self.substitute(3, array_node[str(idx + 1)])
        return v

    def substitute(self, syntax, node, origin=None):
        if node.is_compound():
            self.error(node, "expected a string or integer")
        o = str(node.value())
        r = self.substitute2(syntax, node, o, origin)
        if o != r:
            self.log(3, 'Substitute(%s -> %s)' % (repr(o), repr(r)))
        return r

    def substitute2(self, syntax, node, s, origin=None):
        s = str(s)
        if self.syntax < syntax:
            return s
        if s.find('${') < 0:
            return s
        if self.syntax < 2:
            self.error(node, "cannot substitute (requires 'Syntax 2')")
        r1 = r"\$\$?{[$.,:;@_a-zA-Z0-9-]+}"
        for m in re.findall(r1, s):
            if m[0:2] == '$$':
                id = m[1:]
                ignore = True
            else:
                id = m
                ignore = False
            if id == '${ConfTopDir}':
                if self.syntax < 3:
                    self.error(node, "cannot substitute ${ConfTopDir} (requires 'Syntax 3')")
                s = s.replace(m, self.topdir())
            elif id == '${ConfDir}':
                if self.syntax < 3:
                    self.error(node, "cannot substitute ${ConfDir} (requires 'Syntax 3')")
                s = s.replace(m, self.cfgdir())
            elif id.startswith('${var:'):
                v = id[6:-1]
                if not v in self.var:
                    if not ignore:
                        raise UcmError("variable ${var:%s} is not defined" % v)
                else:
                    s = s.replace(m, self.var[v])
            if self.verify is None:
                continue
            if id == '${ConfName}':
                confname = os.path.split(self.filename)[1]
                s = s.replace(m, confname)
            elif id == '${CardId}':
                s = s.replace(m, self.verify.id)
            elif id == '${CardDriver}':
                s = s.replace(m, self.verify.driver)
            elif id == '${CardName}':
                s = s.replace(m, self.verify.name)
            elif id == '${CardLongName}':
                s = s.replace(m, self.verify.longname)
            elif id == '${CardComponents}':
                s = s.replace(m, self.verify.components)
            elif id == '${CardNumber}':
                if self.syntax < 3:
                    self.error(node, "cannot substitute ${CardNumber} (requires 'Syntax 3')")
                s = s.replace(m, str(self.verify.card))
            elif id.startswith('${env:') or id.startswith('${sys:'):
                r = self.getsvalue2(node, id[2:5], id[6:-1], ignore)
                s = s.replace(m, r)
            elif id.startswith('${CardIdByName:'):
                r = self.getsvalue2(node, id[2:14], id[15:-1], ignore)
                s = s.replace(m, r)
            elif id.startswith('${CardNumberByName:'):
                r = self.getsvalue2(node, id[2:18], id[19:-1], ignore)
                s = s.replace(m, r)
        return s

    def getsvalue2(self, node, cmd, arg, ignore):
        if arg[0] == '$':
            if not arg[1:] in self.var:
                if ignore:
                    return ''
                raise UcmError("variable ${var:%s} is not defined" % arg[1:])
            arg = self.var[arg[1:]]
        if not arg is None:
            r = getattr(self.verify, 'get%s' % cmd)(arg)
            if r is None:
                self.warning(node, "substitution for ${%s:%s} is not available (%s)" % (cmd, arg, repr(self.verify)))
                return "****unknown****"
            return r
        return ''

    def merge_config(self, dst, src, before_node, after_node):

        def get_position_node(node, what):
            if not node or not snode.id in node:
                return None
            n = node[snode.id]
            if not n is None and not n.is_string():
                self.error(node, '%s node has not a string value', what)
            id = n.value()
            if not id in dnode:
                if dnode.is_array():
                    s = 'array(0...%s)' % (len(dnode) - 1)
                else:
                    s = dnode.keys()
                self.error(node, 'identifier %s not found in parent compound (%s)', repr(id), s)
            return dnode[id]

        def unique_id(node1, node2):
            if not self.verify:
                id = node2.id
                idx = 0
                while node2 in node1:
                    node2.set_id(id + '#' + str(idx))
                    idx += 1

        def do_substitute(node):
            if self.syntax < 3:
                return
            node.set_id(self.substitute2(self.syntax, node, node.id))
            if node.is_string():
                node.val = self.substitute2(self.syntax, node, node.val)
            elif node.is_compound():
                for node2 in node:
                    do_substitute(node2)

        if not src.is_compound():
            self.error(nodes, "merge block is not a compound")
        do_substitute(src)
        for snode in src:
            if not snode.id:
                snode.remove()
                dst.add(snode)
                continue
            else:
                dnode = dst.search(snode.id)
                if dnode is None:
                    snode.remove()
                    dst.add(snode)
                    continue
            if not snode.is_compound():
                if not self.verify and snode.type_compare(dnode):
                    snode.remove()
                    unique_id(dst, snode)
                    dst.add(snode)
                    continue
                else:
                    self.error(snode, 'compound type expected for the merged block')
            before = get_position_node(before_node, 'Before')
            after = get_position_node(after_node, 'After')
            if (not before is None) and (not after is None):
                self.error('both Before and After identifiers in the If or Include block')
            array = False
            idx = 0
            if snode.is_array():
                if not dnode.is_array():
                    self.error(snode, 'source and destination nodes must be arrays!')
                array = True
                for ctx in dnode:
                    ctx.set_id('_tmp_%s' % idx)
                    idx += 1
            for ctx in snode:
                ctx.remove()
                if array:
                    ctx.set_id("_tmp_%s" % idx)
                    idx += 1
                if not before is None:
                    unique_id(before.parent, ctx)
                    before.add_before(ctx)
                    before = None
                    after = ctx
                elif not after is None:
                    unique_id(after.parent, ctx)
                    after.add_after(ctx)
                    after = ctx
                else:
                    unique_id(dnode, ctx)
                    if ctx in dnode:
                        snode2 = AlsaConfigUcm(snode)
                        snode2.set_id('__merge__')
                        snode2.make_compound()
                        snode2.add(ctx)
                        self.merge_config(dnode, snode2, None, None)
                    else:
                        dnode.add(ctx)
            if array:
                idx = 0
                for ctx in dnode:
                    ctx.set_id(str(idx))
                    idx += 1

    def condition_ControlExists(self, node):
        control = self.substitute(2, node['Control'])
        c = AlsaControl()
        c.parse(control)
        r = False
        if self.verify:
            r = self.verify.control_exists(c)
        self.log(2, "ControlExists(%s): %s", repr(control), r)
        return r

    def condition_String(self, node):
        if 'Haystack' in node or 'Needle' in node:
            haystack = self.substitute(0, node['Haystack'])
            needle = self.substitute(0, node['Needle'])
            r = haystack.find(needle) >= 0
            self.log(2, "Contains(%s, %s): %s", repr(haystack), repr(needle), r)
        elif 'String1' in node or 'String2' in node:
            string1 = self.substitute(0, node['String1'])
            string2 = self.substitute(0, node['String2'])
            r = string1 == string2
            self.log(2, "IsEqual(%s, %s): %s", repr(string1), repr(string2), r)
        elif 'Empty' in node:
            if self.syntax < 3:
                self.error(node, 'Empty condition is not supported (requires syntax 3+)')
            empty = self.substitute(0, node['Empty'])
            r = not empty
            self.log(2, "Empty(%s): %s", repr(empty), r)
        else:
            self.error(node, 'Empty condition')
        return r

    def condition_RegexMatch(self, node):
        rstr = self.substitute(0, node['Regex'])
        str = self.substitute(0, node['String'])
        m = re.search(rstr, str)
        r = not m is None
        self.log(2, "RegexMatch(%s, %s): %s", repr(rstr), repr(str), r)
        return r

    def condition_ran(self, condition_node, result, true_node, false_node, origin):
        """A notifier that the condition was run to override."""
        pass

    def evaluate_condition(self, condition_node, origin):
        try:
            type = condition_node['Type']
            if not type.is_string():
                self.error(type, 'is not a string')
            type = type.value()
        except:
            self.error(condition_node, "has not 'Type' field")
        for node in condition_node:
            self.validate('Condition%s' % type, node)
        return getattr(self, 'condition_%s' % type)(condition_node)

    def evaluate_if(self, if_node, origin=None):

        def append_nodes(nodes, before_node, after_node):
            if not nodes.is_compound():
                self.error(nodes, "True or False block is not a compound")
            self.merge_config(if_node.parent, nodes, before_node, after_node)

        if self.syntax < 2:
            self.error(if_node, "If is not supported (requires 'Syntax 2')")

        r = False
        for node in if_node:
            self.log(2, "Evaluate if '%s'", node.id)
            if not 'Condition' in node:
                self.error(node, "If requires condition section")
            condition_node = None
            true_node = None
            false_node = None
            before_node = None
            after_node = None
            for node2 in node:
                id = self.validate('If', node2)
                if id == 'Condition':
                    condition_node = node2
                elif id == 'True':
                    true_node = node2
                elif id == 'False':
                    false_node = node2
                elif id == 'Before':
                    before_node = node2
                elif id == 'After':
                    after_node = node2
            result = self.evaluate_condition(condition_node, origin)
            self.condition_ran(condition_node, result, true_node, false_node, origin)
            if true_node is None and false_node is None:
                self.error(if_node, 'True or False block is not defined')
            if (result or not self.verify) and not true_node is None:
                self.evaluate_inplace(true_node, origin)
                append_nodes(true_node, before_node, after_node)
            if (not result or not self.verify) and not false_node is None:
                self.evaluate_inplace(false_node, origin)
                append_nodes(false_node, before_node, after_node)
            node.remove()
            r = True

        return r

    def invalid_filename(self, filename):
        return False

    def evaluate_include(self, inc_node, origin=None):
        if self.syntax < 3:
            self.error(inc_node, "Include is not supported (requires 'Syntax 3')")
        r = False
        for node in inc_node:
            self.log(2, "Evaluate include '%s'", node.id)
            ctx_node = None
            before_node = None
            after_node = None
            for node2 in node:
                id = self.validate('Include', node2)
                if id == 'File':
                    ctx_node = node2
                elif id == 'Before':
                    before_node = node2
                elif id == 'After':
                    after_node = node2
            origin_text = node.origin
            node.remove()
            if ctx_node is None:
                self.error(inc_node, 'File string is not defined')
            filename = self.substitute(0, ctx_node)
            if filename[0] != '/':
                filename = self.cfgdir() + '/' + filename
            else:
                filename = self.topdir() + '/' + filename[1:]
            if not self.verify and self.invalid_filename(filename):
                continue
            nodes = AlsaConfigUcm()
            self.log(2, "Include %s, file '%s'", node.full_id(), self.shortfn(filename))
            nodes.load(filename, origin_text + '.')
            self.evaluate_inplace(nodes, origin)
            if not nodes.is_compound():
                self.error(ctx_node, 'included block is not a compound')
            self.merge_config(inc_node.parent, nodes, before_node, after_node)
            r = True
        return r

    def evaluate_define(self, def_node, origin=None):
        if self.syntax < 3:
            self.error(def_node, "Define is not supported (requires 'Syntax 3')")
        ret = False
        for node in def_node:
            r = self.substitute(0, node, origin)
            self.var[node.id] = r
            self.log(2, "Define.%s = %s", node.id, r)
            ret = True
        return ret

    def evaluate_defineregex(self, re_node, origin=None):
        if self.syntax < 3:
            self.error(re_node, "DefineRegex is not supported (requires 'Syntax 3')")
        ret = False
        for node in re_node:
            if not node.is_compound():
                self.error(node, "DefineRegex must be compound")
            string = None
            reg = None
            flags = ''
            for node2 in node:
                id = self.validate('DefineRegex', node2)
                if id == 'String':
                    string = self.substitute(0, node2)
                elif id == 'Regex':
                    reg = self.substitute(0, node2)
                elif id == 'Flags':
                    flags = node2.value().tolower()
            if string is None:
                self.error(node, "DefineRegex must contain 'String'")
            if reg is None:
                self.error(node, "DefineRegex must contain 'Regex'")
            rflags = 0
            if flags:
                if 'i' in flags:
                    rflags |= re.IGNORECASE
            node.remove()
            m = re.match('.*' + reg, string)
            if not m:
                continue
            self.log(2, "DefineRegex.%s = %s", node.id, m.group(0))
            self.var[node.id] = m.group(0)
            g = m.groups()
            idx = 1
            for a in g:
                self.log(2, "DefineRegex.%s%s = %s", node.id, str(idx), a)
                self.var[node.id + str(idx)] = a
                idx += 1
            ret = True
        return ret

    def evaluate_inplace(self, top_node, origin=None):
        define_flag = True
        defineregex_flag = True
        if_flag = True
        include_flag = True
        while define_flag or defineregex_flag or if_flag or include_flag:
            define_flag = False
            defineregex_flag = False
            include_flag = False
            if_flag = False
            for node in top_node:
                id = self.get_id(node)
                if id == 'Define':
                    if self.evaluate_define(node, origin):
                        define_flag = True
                    node.remove()
            for node in top_node:
                id = self.get_id(node)
                if id == 'DefineRegex':
                    if self.evaluate_defineregex(node, origin):
                        defineregex_flag = True
                    node.remove()
            for node in top_node:
                id = self.get_id(node)
                if id == 'Include':
                    if self.evaluate_include(node, origin):
                        include_flag = True
                    node.remove()
            if include_flag:
                continue
            for node in top_node:
                id = self.get_id(node)
                if id == 'If':
                    if self.evaluate_if(node, origin):
                        if_flag = True
                    node.remove()

    def load_use_case_top(self, compound):
        verb = None
        for node in compound:
            id = self.validate('SectionUseCase', node)
            if id == 'File':
                verb = UcmVerb(self)
                filename = self.substitute(3, node)
                if self.invalid_filename(filename):
                    continue
                verb.load_verb(self.substitute2(3, compound, compound.id), filename)
        if verb is None:
            self.error(compound, "field 'File' not found")
        self.verbs.append(verb)

    def indent_check(self, filename):
        fp = open(filename)
        lineno = 1
        while 1:
            line = fp.readline()
            if not line:
                break
            if line.startswith(' ') and (line.startswith('  ') or len(line) < 3):
                self.error(None, "%s:%d: Wrong indentation (use tabs to save space!)" % (filename, lineno))
            if line.endswith(' ') or line.endswith('\t'):
                self.error(None, "%s:%d: Trailing space or tabelator!" % (filename, lineno))
            lineno += 1

    def load(self, filename):
        """Load ucm configuration from filename."""
        self.reset()
        filename = os.path.abspath(filename)
        self.filename = filename
        self.indent_check(filename)
        aconfig = AlsaConfigUcm()
        self.log(1, "Device file '%s'", self.shortfn())
        aconfig.load(filename)
        if 'Syntax' in aconfig:
            self.syntax = int(aconfig['Syntax'].value())
        self.evaluate_inplace(aconfig)
        for node in aconfig:
            id = self.validate('master', node)
            if id == 'Syntax':
                continue
            elif id == 'Comment':
                self.comment = node.value()
            elif id == 'SectionUseCase':
                for node2 in node:
                    self.load_use_case_top(node2)
            elif id == 'ValueDefaults':
                self.values = UcmValue(self)
                self.values.load_value(node, {'Linked':'intstring'})
            elif id == 'BootSequence':
                self.boot = self.load_sequence(node)

    def check(self):
        if not self.verify:
            raise UcmError("cannot verify abstract contents")
        for verb in self.verbs:
            verb.check()

    def dump(self):
        r = 'File: %s\n' % self.filename
        for verb in self.verbs:
            v = verb.dump()
            if v:
                r += '\n'.join(map(lambda x: '  ' + x, v.splitlines())) + '\n'
        return r

    def get_file_list1(self, path):
        card = self.verify
        l1 = path + '/' + ucm_safe_fn(card.driver) + '/' + ucm_safe_fn(card.longname) + '.conf'
        l2 = path + '/' + ucm_safe_fn(card.driver) + '/' + ucm_safe_fn(card.driver) + '.conf'
        return [l1, l2]

    def get_file_list(self, path):

        def list_topdir(self):
            return os.path.split(fn)[0]

        self.reset()
        fn = os.path.abspath(os.path.realpath(path + '/ucm.conf'))
        if not os.path.exists(fn):
            return self.get_file_list1(path)
        c = AlsaConfigUcm()
        self.filename = fn
        self.cfgdir = types.MethodType(list_topdir, self)
        self.topdir = types.MethodType(list_topdir, self)
        c.load(fn)
        if not 'Syntax' in c:
            self.error(c, 'Syntax field is missing in toplevel file')
        self.syntax = int(c['Syntax'].value())
        if self.syntax < 2:
            self.error(c, 'Minimal supported Syntax is 2')
        self.evaluate_inplace(c)
        r = []
        for node in c:
            id = self.validate('top', node)
            if id == 'UseCasePath':
                for node2 in node:
                    dir = None
                    file = None
                    version = 2
                    for node3 in node2:
                        self.validate('UseCasePath', node3)
                        if node3.id == 'Version':
                            version = int(self.substitute(0, node3))
                        elif node3.id == 'Directory':
                            dir = self.substitute(0, node3)
                        elif node3.id == 'File':
                            file = self.substitute(0, node3)
                    if version < 2:
                        continue
                    fn2 = path + '/' + dir + '/' + file
                    if r and fn2 in r:
                        continue
                    r.append(path + '/' + dir + '/' + file)
        self.cfgdir = types.MethodType(Ucm.cfgdir, self)
        self.topdir = types.MethodType(Ucm.topdir, self)
        return r

def ucm_env_get(alsa_config_path):
    env = 'ALSA_CONFIG_DIR' in os.environ and os.environ['ALSA_CONFIG_DIR'] or None
    os.environ['ALSA_CONFIG_DIR'] = os.path.abspath(os.path.realpath(alsa_config_path))
    return env

def ucm_env_put(env):
    if not env is None:
        os.environ['ALSA_CONFIG_DIR'] = env

def ucm_safe_fn(filename):
    while filename[0] == '.':
        filename = filename[1:]
    return filename.replace('/', '-')

def ucm_get_configs(path, short=False, link=True):
    """Walk through UCM configurations specified by path."""

    def one(driver):
        dir = path + '/' + driver
        for cfg in os.listdir(dir):
            if cfg.startswith('.') or (not cfg.endswith('.conf')):
                continue
            f = dir + '/' + cfg
            if not link and os.path.islink(f):
                continue
            fp = open(f, 'r')
            ctx = ''
            while 1:
                add = fp.read(8192)
                if not add:
                    break
                ctx += add
            fp.close()
            if ctx.find('Syntax') < 0:
                continue
            if short:
                f = driver + '/' + cfg
            r.append(f)

    r = []
    path = os.path.abspath(os.path.realpath(path))
    if not os.path.isdir(path):
        raise UcmError("path '%s' is not a directory" % path)
    for name in os.listdir(path):
        if name.startswith('.') or name.endswith('~'):
            continue
        fpath = path + '/' + name
        if not link and os.path.islink(fpath):
            continue
        if os.path.isdir(fpath):
            one(name)
    return r
