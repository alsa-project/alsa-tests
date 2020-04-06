#! /usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-or-later

# ucmlib.py - ALSA Use Case Manager routines
# Copyright (c) 2020 Jaroslav Kysela <perex@perex.cz>

import os
import sys
import re
from aconfig import AlsaConfig

VALID_ID_LISTS = {
    'top': {
        'Syntax': 'integer',
        'Comment': 'string',
        'SectionDefaults': 'compound',
        'SectionUseCase': 'compound',
        'ValueDefaults': 'compound'
    },
    'If': {
        'Condition': 'compound',
        'True': 'compound',
        'False': 'compound',
        'After': 'compound',
        'Before': 'compound'
    },
    'ConditionControlExists': {
        'Type': 'string',
        'Control': 'string',
        'ControlEnum': 'string'
    },
    'ConditionString': {
        'Type': 'string',
        'Haystack': 'string',
        'Needle': 'string'
    },
    'SectionUseCase': {
        'File': 'string',
        'Comment': 'string'
    },
    'UseCaseFile': {
        'If': 'compound',
        'SectionVerb': 'compound',
        'SectionDevice': 'compound',
        'RenameDevice': 'compound',
        'RemoveDevice': 'compound'
    },
    'SectionVerb': {
        'If': 'compound',
        'Value': 'compound',
        'EnableSequence': 'compound',
        'DisableSequence': 'compound'
    },
    'SectionDevice': {
        'If': 'compound',
        'Comment': 'string',
        'EnableSequence': 'compound',
        'DisableSequence': 'compound',
        'ConflictingDevice': 'compound',
        'SupportedDevice': 'compound',
        'Value': 'compound'
    },
    'Value': {
        'If': 'compound',
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
    'HDMI'
}

def dict_array_append(d, key, val):
    if not key in d:
        d[key] = []
    d[key].append(val)

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

class UcmCompoundIterator:

    def __init__(self, base, extra):
        """Iterate through base and then through extra."""
        self.base = base
        self.extra = extra
        self.baseiter = iter(base)
        self.extraiter = None

    def __iter__(self):
        return self

    def __next__(self):
        if not self.baseiter is None:
            try:
                return next(self.baseiter)
            except StopIteration:
                self.baseiter = None
        if self.baseiter is None:
            if self.extraiter is None:
                self.extraiter = iter(self.extra)
            return next(self.extraiter)

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

    def validate(self, what, node, prefix=''):
        return self.parent.validate(what, node)

    def load_value(self, value_node):
        add = []
        for node in UcmCompoundIterator(value_node, add):
            self.validate('Value', node)
            if node.id == 'If':
                self.parent.evaluate_if(node, add, self)
            self.values[node.id] = node.value()

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

    def validate(self, what, node, prefix=''):
        prefix = "%s(Device=%s) " % (prefix, self.name)
        return self.verb.validate(what, node, prefix)

    def shortfn(self):
        return self.verb.shortfn()

    def getval(self, name):
        if self.values and name in self.values:
            return self.values[name]
        return self.verb.getval(name)

    def getintval(self, name):
        v = self.getval(name)
        return v is None and None or int(v)

    def evaluate_if(self, if_node, add, origin=None):
        return self.ucm.evaluate_if(if_node, add, origin and origin or self)

    def load_array(self, array_node):
        v = array_node.value()
        if type(v) != type([]):
            self.error(array_node, "is not array")
        return v

    def load_device(self, device_node):
        self.log(1, "Device '%s'", device_node.id)
        self.reset()
        self.name = device_node.id
        add = []
        for node in UcmCompoundIterator(device_node, add):
            self.validate('SectionDevice', node)
            if node.id == 'If':
                self.ucm.evaluate_if(node, add, self)
            elif node.id == 'Comment':
                self.comment = node.value()
            elif node.id == 'EnableSequence':
                self.enable = self.load_array(node)
            elif node.id == 'DisableSequence':
                self.disable = self.load_array(node)
            elif node.id == 'ConflictingDevice':
                self.conflicting = self.load_array(node)
            elif node.id == 'SupportedDevice':
                self.supported = self.load_array(node)
            elif node.id == 'Value':
                self.values = UcmValue(self)
                self.values.load_value(node)

    def get_pcm(self, stream):
        name = stream + 'PCM'
        if not self.getval(name):
            return None
        d = {}
        d['prio'] = self.getintval(stream + 'Priority')
        return d

    def check_pcm_name(self, name):
        r1 = r"^(plug|)hw:\${CardId}(,[0-9]+|)$"
        m = re.match(r1, name)
        if not m:
            self.error(0, 'PCM name %s is invalid' % repr(name))
        r2 = r"^(plug|)hw:\${CardId},0$"
        m = re.match(r2, name)
        if m:
            self.warning(0, 'PCM name %s can be trucated (remove trailing zero /,0/)' % repr(name))

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
                v = self.getval(pname)
                if v is None:
                    self.error(0, '%s not defined' % pname)
                if type(v) == type(''):
                    self.warning(0, '%s is not an integer' % pname)
                cname = prefix + 'Channels'
                v = self.getval(cname)
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
        self.devices = {}

    def validate(self, what, node, prefix=''):
        prefix = "%s(Verb=%s) " % (prefix, self.name)
        return self.ucm.validate(what, node, prefix)

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

    def evaluate_if(self, if_node, add, origin=None):
        return self.ucm.evaluate_if(if_node, add, origin and origin or self)

    def load_array(self, array_node):
        v = array_node.value()
        if type(v) != type([]):
            self.error(array_node, "is not array")
        return v

    def section_verb(self, node):
        add = []
        for node in UcmCompoundIterator(node, add):
            self.validate('SectionVerb', node)
            if node.id == 'If':
                self.evaluate_if(node, add)
            elif node.id == 'EnableSequence':
                self.enable = self.load_array(node)
            elif node.id == 'DisableSequence':
                self.disable = self.load_array(node)
            elif node.id == 'Value':
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
        topdir = self.ucm.topdir()
        if filename[0] != '/':
            filename = self.ucm.cfgdir() + '/' + filename
        aconfig = AlsaConfig()
        self.log(1, "Verb '%s', file '%s'", verbname, self.ucm.shortfn(filename))
        aconfig.load(filename)
        rename_dict = {}
        remove_list = {}
        add = []
        for node in UcmCompoundIterator(aconfig, add):
            self.validate('UseCaseFile', node)
            if node.id == 'If':
                self.evaluate_if(node, add)
            elif node.id == 'SectionVerb':
                self.section_verb(node)
            elif node.id == 'SectionDevice':
                for node2 in node:
                    dev = UcmDevice(self)
                    dev.load_device(node2)
                    self.devices[dev.name] = dev
            elif node.id == 'RenameDevice':
                rename_dict = node.value()
            elif node.id == 'RemoveDevice':
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

    def id(self):
        return self.shortfn(self.filename)

    def log(self, lvl, msg, *args):
        """Write a log message (override)."""
        pass

    def error(self, node, msg, *args):
        if node:
            raise UcmError("%s: %s %s" % (self.id(), node.full_id(), msg % args))
        else:
            raise UcmError("%s: %s" % (self.id(), msg % args))

    def warn(self, msg, *args):
        """Write a warning message (override)."""
        pass

    def warning(self, node, msg, *args):
        if node:
            self.warn("%s: %s %s", self.id(), node.full_id(), msg % args)
        else:
            self.warn("%s: %s", self.id(), msg % args)

    def reset(self):
        self.syntax = 0
        self.comment = None
        self.verbs = []
        self.values = None

    def cfgdir(self):
        return os.path.split(self.filename)[0]

    def topdir(self):
        return os.path.split(self.cfgdir())[0]

    def shortfn(self, filename=None):
        if filename is None:
            filename = self.filename
        topdir = self.topdir()
        if not filename.startswith(topdir):
            raise UcmError("shortfn mismatch '%s' / '%s'" % (topdir, filename))
        return filename[len(topdir)+1:]

    def validate(self, what, node, prefix=''):
        if not what in VALID_ID_LISTS:
            raise UcmError("%sdefine validity list for '%s'" % (prefix, what))
        vlist = VALID_ID_LISTS[what]
        if not node.id in vlist:
            self.error(node, "%sfield is not known" % prefix)
        t = vlist[node.id]
        t2 = node.typename()
        if t == 'intstring':
            if t2 == 'string':
                try:
                    val = int(node.value())
                except:
                    self.error(node, "%svalue %s cannot be converted to integer" % (prefix, repr(node.value())))
                return
            t = 'integer'
        if t != node.typename():
            self.error(node, "%sis not type %s (has type '%s')" % (prefix, repr(t), node.typename()))

    def getval(self, name):
        if self.values and name in self.values:
            return self.values[name]
        return None

    def substitute(self, s):
        if self.verify is None:
            return s
        if s.find('${') < 0:
            return s
        r1 = r"\${(env|sys):(.*)}"
        for m in re.findall(r1, s):
            raise UcmError("substitution for ${%s:%s} is not implemented" % m)
        confname = os.path.split(self.filename)[1]
        s = s.replace('${ConfName}', confname). \
              replace('${CardId}', self.verify.id). \
              replace('${CardDriver}', self.verify.driver). \
              replace('${CardName}', self.verify.name). \
              replace('${CardLongName}', self.verify.longname). \
              replace('${CardComponents}', self.verify.components)
        return s

    def condition_ControlExists(self, node):
        control = node['Control'].value()
        c = AlsaControl()
        c.parse(control)
        r = False
        if self.verify:
            r = self.verify.control_exists(c)
        self.log(2, "ControlExists(%s): %s", repr(control), r)
        return r

    def condition_String(self, node):
        haystack = self.substitute(node['Haystack'].value())
        needle = self.substitute(node['Needle'].value())
        r = haystack.find(needle) >= 0
        self.log(2, "Contains(%s, %s): %s", repr(haystack), repr(needle), r)
        return r

    def condition_ran(self, condition_node, result, origin):
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
        r = getattr(self, 'condition_%s' % type)(condition_node)
        self.condition_ran(condition_node, r, origin)
        return r

    def evaluate_if(self, if_node, add, origin=None):

        def append_nodes(nodes):
            if not nodes.is_compound():
                self.error(nodes, "True or False block is not a compound")
            for node in nodes:
                add.append(node)

        add1 = []
        for node in UcmCompoundIterator(if_node, add1):
            self.log(2, "Evaluate if '%s'", node.id)
            result = None
            true_node = None
            false_node = None
            for node2 in node:
                self.validate('If', node2)
                if node2.id == 'If':
                    self.evaluate_if(node2, add1)
                elif node2.id == 'Condition':
                    result = self.evaluate_condition(node2, origin)
                elif node2.id == 'True':
                    true_node = node2
                elif node2.id == 'False':
                    false_node = node2
            if true_node is None and false_node is None:
                self.error(if_node, 'True or False block is not defined')
            if (result or not self.verify) and not true_node is None:
                append_nodes(true_node)
            if (not result or not self.verify) and not false_node is None:
                append_nodes(false_node)

    def load_use_case_top(self, compound):
        verb = None
        for node in compound:
            self.validate('SectionUseCase', node)
            if node.id == 'File':
                verb = UcmVerb(self)
                verb.load_verb(compound.id, node.value())
        if verb is None:
            self.error(compound, "field 'File' not found")
        self.verbs.append(verb)

    def load(self, filename):
        """Load ucm configuration from filename."""
        self.reset()
        filename = os.path.abspath(filename)
        self.filename = filename
        aconfig = AlsaConfig()
        self.log(1, "Device file '%s'", self.shortfn())
        aconfig.load(filename)
        add = []
        for node in UcmCompoundIterator(aconfig, add):
            self.validate('top', node)
            if node.id == 'If':
                self.evaluate_if(node, add)
            if node.id == 'Syntax':
                self.syntax = node.value()
            elif node.id == 'Comment':
                self.comment = node.value()
            elif node.id == 'SectionUseCase':
                for node2 in node:
                    self.load_use_case_top(node2)
            elif node.id == 'ValueDefaults':
                self.values = UcmValue(self)
                self.values.load_value(node)                

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
