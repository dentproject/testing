"""database.py

Digested information of the model

  pacakge - collection of modules that represents the whole system.
   +- modules - collection of classes and types that make up a sub system
    +- classes - single funtional entity
      +- members - members of the classes
     - types  - custom data types.
     - commands - command classes
      +- members - parameters of the commands
     - test_cases - list of test cases
"""

import re


def uppercase(string):
    return str(string).upper()


def camelcase(string):
    string = re.sub(r'^[\-_\.]', '', str(string))
    if not string:
        return string
    return uppercase(string[0]) + re.sub(
        r'[\-_\.\s]([a-z])', lambda matched: uppercase(matched.group(1)), string[1:]
    )


class TypeMember(object):
    def __init__(self, typ, name, ydata):
        self._typ = typ
        self._ydata = ydata
        self.name = name
        self.desc = ydata['desc'] if 'desc' in ydata else ''
        self.type = ydata['type'] if 'type' in ydata else None

    def to_dict(self):
        return {
            'tmbr_name': self.name,
            'tmbr_desc': self.desc,
            'tmbr_type': self.type,
        }

    def validate(self):
        if self.type and ':' in self.type:
            mod, typ = self.type.split(':')
            self.type = self._typ._mod._pkg.lookup_type(mod, typ)

    def post_validate(self):
        pass


class Type(object):
    def __init__(self, mod, name, ydata, fname):
        self._mod = mod
        self._ydata = ydata
        self._yfile = fname
        self.name = name
        self.desc = ydata['desc'] if 'desc' in ydata else ''
        self.type = ydata['type']
        self.members = (
            [TypeMember(self, mdata['name'], mdata) for mdata in ydata['members']]
            if 'members' in ydata
            else []
        )

    def to_dict(self):
        return {
            't_name': self.name,
            't_desc': self.desc,
            't_type': self.type,
            't_members': {m.name: m.to_dict() for m in self.members},
        }

    def validate(self):
        for m in self.members:
            m.validate()
        if ':' in self.type:
            mod, typ = self.type.split(':')
            self.type = self._mod._pkg.lookup_type(mod, typ)

    def post_validate(self):
        for m in self.members:
            m.post_validate()


class TestCase(object):
    def __init__(self, test, name, ydata):
        self._test = test
        self._ydata = ydata
        self.name = name
        self.template = ydata['template'] if 'template' in ydata else ''
        self.cls = ydata['class'] if 'class' in ydata else None
        self.args = ydata['args'] if 'args' in ydata else ''

    def to_dict(self):
        return {
            'tc_name': self.name,
            'tc_template': self.template,
            'tc_class' : self.cls.to_dict() if self.cls else '',
            'tc_args' : self.args,
        }

    def validate(self):
        if self.cls and ':' in self.cls:
            pkg, mod, cls = self.cls.split(':')
            self.cls = self._test._mod._pkg._db[pkg].lookup_class(mod, cls)


class Test(object):
    def __init__(self, mod, name, ydata, fname):
        self._mod = mod
        self._ydata = ydata
        self._yfile = fname
        self.name = name
        self.test_cases = (
            [TestCase(self, mdata['name'], mdata) for mdata in ydata['test_cases']]
            if 'test_cases' in ydata
            else []
        )

    def to_dict(self):
        return {
            'test_name': self.name,
            'test_cases': {t.name: t.to_dict() for t in self.test_cases},
        }

    def validate(self):
        for t in self.test_cases:
            t.validate()


class ClassMember(object):
    def __init__(self, cls, name, ydata):
        self._cls = cls
        self._ydata = ydata
        self.name = name
        self.desc = ydata['desc'] if 'desc' in ydata else ''
        self.type = ydata['type'] if 'type' in ydata else None
        self.cls = ydata['cls'] if 'cls' in ydata else None
        self.mandatory = ydata['mandatory'] if 'mandatory' in ydata else []
        self.key = (True if ydata['key'] == 'True' else False) if 'key' in ydata else False
        self.readonly = (True if ydata['readonly'] == 'True' else False) if 'readonly' in ydata else False

    def to_dict(self):
        return {
            'cmbr_name': self.name,
            'cmbr_desc': self.desc,
            'cmbr_type': self.type,
        }

    def validate(self):
        if self.type and ':' in self.type:
            mod, typ = self.type.split(':')
            self.type = self._cls._mod._pkg.lookup_type(mod, typ)
        if self.cls and ':' in self.cls:
            pkg, mod, cls = self.cls.split(':')
            self.cls = self._cls._mod._pkg._db[pkg].lookup_class(mod, cls)

    def post_validate(self):
        pass


class ClassCommand(object):
    def __init__(self, cls, name, ydata):
        self._cls = cls
        self._ydata = ydata
        self.name = name
        self.apis = ydata['apis']
        self.cmd = ydata['cmd'][0] if 'cmd' in ydata else ''
        self.desc = ydata['desc'] if 'desc' in ydata else ''

    def to_dict(self):
        return {
            'cmd_name': self.name,
            'cmd_apis': self.apis,
            'cmd': self.cmd,
            'cmd_desc': self.desc,
        }

    def validate(self):
        pass

    def post_validate(self):
        if 'params' in self._ydata:
            self.params = []
            for p in self._ydata['params']:
                if p not in self._cls.implements.members_dct:
                    self.params.append(p)
                else:
                    self.params.append(self._cls.implements.members_dct[p])
        else:
            self.params = self._cls.implements.members if self._cls.implements else []


class Class(object):
    def __init__(self, mod, name, ydata, fname):
        self._mod = mod
        self._ydata = ydata
        self._yfile = fname
        self.name = name
        self.desc = ydata['desc'] if 'desc' in ydata else ''
        self.members = (
            [ClassMember(self, mdata['name'], mdata) for mdata in ydata['members']]
            if 'members' in ydata
            else []
        )
        self.members_dct = {m.name:m for m in self.members}
        self.apis = ydata['apis'] if 'apis' in ydata else ['add', 'del', 'get', 'dump']
        self.implements = ydata['implements'] if 'implements' in ydata else None
        # indicates how many instances the object can have
        self.singleton = ydata['singleton'] if 'singleton' in ydata else False
        self.local = ydata['local'] if 'local' in ydata else False
        self.platforms = ydata['platforms'] if 'platforms' in ydata else []
        self.commands = (
            [ClassCommand(self, mdata['name'], mdata) for mdata in ydata['commands']]
            if 'commands' in ydata
            else []
        )
        self.implemented_by = []
        self.classes = [Class(mod, s['name'], s, fname) for s in ydata['classes']] if 'classes' in ydata else []

    def to_dict(self):
        return {
            'cls_mod_name' : self._mod.name,
            'cls_name': self.name,
            'cls_cc_name': camelcase(self.name),
            'cls_desc' : self.desc,
            'cls_members': {m.name: m.to_dict() for m in self.members},
            'cls_apis': self.apis,
        }

    def validate(self):
        for m in self.members:
            m.validate()
        for c in self.commands:
            c.validate()
        if self.implements:
            pkg, mod, cls = self.implements.split(':')
            self.implements = self._mod._pkg._db[pkg].lookup_class(mod, cls)
            if self not in self.implements.implemented_by:
                self.implements.implemented_by.append(self)
        for s in self.classes: s.validate()

    def post_validate(self):
        for m in self.members:
            m.post_validate()
        for c in self.commands:
            c.post_validate()
        for s in self.classes: s.post_validate()


class Module(object):
    def __init__(self, pkg, name, ydata, fname):
        self._pkg = pkg
        self._ydata = ydata
        self.name = name
        self.desc = ydata['desc'] if 'desc' in ydata else ''
        self.classes = (
            [Class(self, cdata['name'], cdata, fname) for cdata in ydata['classes']]
            if 'classes' in ydata
            else []
        )
        self.classes_dct = {c.name: c for c in self.classes}
        self.types = (
            [Type(self, tdata['name'], tdata, fname) for tdata in ydata['types']]
            if 'types' in ydata
            else []
        )
        self.types_dct = {t.name: t for t in self.types}
        self.tests = (
            [Test(self, tdata['name'], tdata, fname) for tdata in ydata['tests']]
            if 'tests' in ydata
            else []
        )
        self.tests_dct = {t.name: t for t in self.tests}

    def append_to_module(self, ydata, fname):
        self.classes += (
            [Class(self, cdata['name'], cdata, fname) for cdata in ydata['classes']]
            if 'classes' in ydata
            else []
        )
        self.types += (
            [Type(self, tdata['name'], tdata, fname) for tdata in ydata['types']]
            if 'types' in ydata
            else []
        )
        self.types_dct = {t.name: t for t in self.types}
        self.classes_dct = {c.name: c for c in self.classes}
        self.tests += (
            [Test(self, tdata['name'], tdata, fname) for tdata in ydata['tests']]
            if 'tests' in ydata
            else []
        )
        self.tests_dct = {t.name: t for t in self.tests}

    def to_dict(self):
        return {
            'mod_name': self.name,
            'mod_desc': self.desc,
            'mod_classes': {c.name: c.to_dict() for c in self.classes},
            'mod_types': {t.name: t.to_dict() for t in self.types},
        }

    def validate(self):
        for t in self.types:
            t.validate()
        for c in self.classes:
            c.validate()
        for t in self.tests:
            t.validate()

    def post_validate(self):
        for t in self.types:
            t.post_validate()
        for c in self.classes:
            c.post_validate()


class Package(object):
    def __init__(self, name, ydata, fname, db):
        self._ydata = ydata
        self._db = db
        self.name = name
        self.modules = {mdata['module']: Module(self, mdata['module'], mdata, fname) for mdata in ydata}

    def append_to_pkg(self, ydata, fname):
        for mdata in ydata:
            mod = mdata['module']
            if mod not in self.modules:
                self.modules[mod] = Module(self, mod, mdata, fname)
            else:
                self.modules[mod].append_to_module(mdata, fname)

    def to_dict(self):
        return {
            'pkg_name': self.name,
            'pkg_modules': {m.name: m.to_dict() for m in self.modules},
        }

    def validate(self):
        for m in self.modules.values():
            m.validate()

    def post_validate(self):
        for m in self.modules.values():
            m.post_validate()

    def lookup_type(self, mod, typ):
        return self.modules[mod].types_dct[typ]

    def lookup_class(self, mod, cls):
        return self.modules[mod].classes_dct[cls]
