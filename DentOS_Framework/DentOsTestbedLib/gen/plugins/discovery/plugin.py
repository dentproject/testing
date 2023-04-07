"""plugin.py

Discovery plugin generates the ReportSchema.py with all schema and setand get methods.
"""

import os

import random
import string

from gen.lib.database import camelcase
from gen.lib.python.pylib import PyClass, PyFile, PyImport, PyLines, PyMethod
from gen.lib.sample_plugin import SamplePlugin
from gen.plugins.discovery.template import (
    discovery_py_header,
    discovery_py_dict_schema_body,
    discovery_py_list_schema_body,
    discovery_py_report_body,
    discover_py_code_template,
    discover_py_code_set_func,
    discover_py_code_set_attr
)


class ReportPyObject(object):
    def __init__(self, pkg, fname):
        self._pkg = pkg
        self._fname = fname
        self._header = [PyLines(lines=tokenize(discovery_py_header % pkg.name))]
        self._imports = []
        self._classes = []
        self._methods = []

    def get_python_type(self, mbr):
        if not isinstance(mbr, str):
            mbr = mbr.type
        if mbr == 'string': return 'str'
        if mbr == 'string_list': return 'str'
        if mbr == 'time_t': return 'str'
        if mbr == 'ip_addr_t': return 'str'
        if mbr == 'mac_t': return 'str'
        return mbr

    def generate_schema_classes(self, parent, name):
        """
        1. Do a level order BFS on visiting on all the classes that has members.
        2. generate the schema and validation classes.
        3. return the classes in reverse order to be generated in the ReportSchema.py
        """
        classes = []
        visited = {}
        queue=[(parent, name)]
        while queue:
            node,name = queue.pop(0)
            if node in visited:
                continue
            visited[node] = True
            # add the members to queue
            args = {}
            members = ''
            for m in node.members:
                mname = ''
                # if this is class type
                if m.cls:
                    # if there are no members in this member then use the correct schema
                    if len(m.cls.members):
                        mname = camelcase(m.cls.name)+('SchemaDict' if m.cls.singleton else 'SchemaList')
                        # need to visit the node
                        queue.append((m.cls, camelcase(m.cls.name)))
                    else:
                        mname = 'LeafSchemaDict'
                elif m.type:
                    mname = self.get_python_type(m.type)
                members += '        "%s":%s,\n' % (m.name, mname)
            if not node.singleton:
                methods = [PyLines(lines=tokenize(discovery_py_list_schema_body % name))]
                classes.append(PyClass(name+'SchemaList',
                                       parent='SchemaList',
                                       methods=methods))
            args['members'] = members
            methods = [PyLines(lines=tokenize(discovery_py_dict_schema_body % args))]
            classes.append(PyClass(name+'SchemaDict',
                                   desc=[PyLines(lines=['    Refer '+node._yfile+' '+node.name])],
                                   parent='SchemaDict',
                                   methods=methods))
        return classes[::-1]

    def generate_code(self):
        self._imports.append(PyImport('io'))
        self._imports.append(PyImport('json'))
        self._imports.append(PyImport('copy'))
        self._imports.append(PyImport('(LeafSchemaDict, SchemaList, SchemaDict, Report)', _from='dent_os_testbed.discovery.Report '))

        # recurse the level from base.

        # discard other accessors
        methods = [PyLines(lines=tokenize(discovery_py_report_body))]
        self._classes.extend(
            self.generate_schema_classes(
                self._pkg.modules['base'].classes_dct['base'],
                'Report'
            )
        )

        self._classes.append(PyClass('ReportSchema', parent='Report',methods=methods))

    def write_file(self):
        p = PyFile(self._header, self._imports, self._classes, self._methods)
        p.write(self._fname)


class DiscoveryModulePyObject(object):
    def __init__(self, cls, parent, fname):
        self._cls = cls
        self._parent = parent
        self._fname = fname
        self._header = [PyLines(lines=tokenize(discovery_py_header % self._cls._yfile))]
        self._imports = []
        self._classes = []
        self._methods = []

    def get_mbr_default(self, mbr):
        if not isinstance(mbr, str):
            mbr = mbr.type
        if mbr == 'string': return "''"
        if mbr == 'string_list': return "''"
        if mbr == 'time_t': return "''"
        if mbr == 'ip_addr_t': return "''"
        if mbr == 'mac_t': return "''"
        if mbr == 'int': return 0
        if mbr == 'float': return 0.0
        return mbr

    def generate_mbr_set_attr(self, cls):
        set_mbr = ''
        args = cls.to_dict()
        args['dst'] = 'dst' if cls.singleton else 'dst[i]'
        args['src'] = '[src]' if cls.singleton else 'src'
        methods = []
        for m in cls.members:
            args['mbr'] = m.name
            if m.cls:
                methods.extend(self.generate_mbr_set_attr(m.cls))
                args['mbr_cls_name'] = m.cls.name
                set_mbr += '    self.set_%(mbr_cls_name)s(%(cls_name)s.get(\'%(mbr)s\', []), %(dst)s.%(mbr)s)\n' % args
                continue
            if m.type not in ['str', 'string', 'int', 'ip_addr_t', 'mac_t', 'float']:
                continue
            args['mbr_default'] = self.get_mbr_default(m)
            set_mbr += discover_py_code_set_attr % args
        args['set_mbr'] = set_mbr
        set_attr_body = tokenize(discover_py_code_set_func % args)
        methods.append(PyMethod('set_'+cls.name, 'self, src, dst', set_attr_body, indent=4))
        return methods

    def generate_code(self):
        self._imports.append(PyImport('Module', _from='dent_os_testbed.discovery.Module '))
        self._imports.append(
            PyImport(
                camelcase(self._cls.name),
                _from='dent_os_testbed.lib.%s.'
                % (self._cls._mod.name)
                + self._cls.name
                + ' ',
            )
        )
        methods = []
        methods.extend(self.generate_mbr_set_attr(self._cls))
        args = self._cls.to_dict()
        args['cname_cc'] = camelcase(self._cls.name)
        args['parent'] = self._parent
        discover_body = tokenize(discover_py_code_template % args)
        methods.append(PyMethod('discover', 'self', discover_body, indent=4, coroutine=True))
        self._classes.append(
            PyClass(camelcase(self._cls.name)+'Mod',
                    parent='Module',
                    methods=methods))

    def write_file(self):
        p = PyFile(self._header, self._imports, self._classes, self._methods)
        p.write(self._fname)


class DiscoveryPlugin(SamplePlugin):
    """
    1. start from the base class under dent package
    2. walk all the members and its types untill we reach the leaf node
    3. keep generating the report.py that can handle set and get operations.
    """
    def __init__(self, name):
        self.name = name

    def generate_code(self, dbs, odir):
        print('Generating Discovery')
        # create the directory
        tdir = os.path.join(odir, 'src/dent_os_testbed/discovery/')
        #gi = os.path.join(tdir, ".gitignore")
        #gd = open(gi, "w")
        if not os.path.exists(tdir):
            os.makedirs(tdir)
            fname = os.path.join(tdir, '__init__.py')
            f = open(fname, 'w')
            f.write("__import__(\"pkg_resources\").declare_namespace(__name__)")
            f.close()
        fname = os.path.join(tdir, 'ReportSchema.py')
        #gd.write("ReportSchema.py\n")
        o = ReportPyObject(dbs['dent'], fname)
        o.generate_code()
        o.write_file()

        tdir = os.path.join(odir, 'src/dent_os_testbed/discovery/modules')
        if not os.path.exists(tdir):
            os.makedirs(tdir)
            fname = os.path.join(tdir, '__init__.py')
            f = open(fname, 'w')
            f.write("__import__(\"pkg_resources\").declare_namespace(__name__)")
            f.close()
        # BFS from base class and create discovery for each class that has implemented by
        visited = {}
        #queue=[(dbs["dent"].modules['base'].classes_dct['duts'],'data["duts"][i]')]
        queue=[(dbs['dent'].modules['base'].classes_dct['duts'],'self.report.duts[i]')]
        while queue:
            (node, parent) = queue.pop(0)
            if node in visited:
                continue
            visited[node] = True
            for m in node.members:
                if not m.cls: continue
                queue.append((m.cls, parent+'.'+m.name))
            if not node.implemented_by: continue
            if 'show' not in node.apis: continue
            # now need to create discovery module
            fname = os.path.join(tdir, 'mod_' + node.name + '.py')
            #gd.write(f"modules/mod_{node.name}.py\n")
            o = DiscoveryModulePyObject(node, parent, fname)
            o.generate_code()
            o.write_file()
        #gd.close()
