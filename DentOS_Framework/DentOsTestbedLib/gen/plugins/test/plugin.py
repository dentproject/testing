"""plugin.py

TestLib plugin to generate common API that can perform operations
on devices in the dent testbed devices.

generates three files for every dent api_class that has command implementation
in platform command model
   src/dent_os_testbed/<module>/<dent_api_class>.yaml
   src/dent_os_testbed/<module>/<platform>/<platform_api_class>.yaml
   src/dent_os_testbed/<module>/<platform>/<pltform_api_class>_impl.yaml

  The test writers would use dent_os_testbed.<module>.<dent_api_class>.NetProdClass.<api>
  to perform operations on the remote devices.

  The plugin also generates unit test code under tests/test_<dent_api_class>.py
"""


import os

import random
import string

from gen.lib.database import camelcase
from gen.lib.python.pylib import PyClass, PyFile, PyImport, PyLines, PyMethod
from gen.lib.sample_plugin import SamplePlugin
from gen.plugins.test.template import (
    py_class_common_format_cmd_case,
    py_class_common_format_cmds,
    py_class_common_format_cmd,
    py_class_common_run_cmd_case,
    py_class_common_run_cmds,
    py_class_common_run_cmd,
    py_class_common_parse_cmd_case,
    py_class_common_parse_cmds,
    py_class_common_parse_cmd,
    py_class_common_impl_form_command,
    py_class_common_run,
    py_class_common_run_api,
    py_header,
    py_impl_class_common_format_cmd,
    py_impl_class_common_run_cmd,
    py_impl_class_common_parse_cmd,
    py_test_code_template,
    py_test_code_two_cmd_template_call,
    py_test_code_two_dev_template_call
)

dent_prefix = 'dent_'
dent_test_prefix = 'test_dent_'


def tokenize(str, by='\n', indent=0):
    """
    split the lines based on by and return a list of lines by indenting with spaces
    """
    if indent == 0:
        return str.split(by)
    return [(' '*indent + s) for s in str.split(by)]


class TestPyObject(object):
    """
    generates the dent PI python files for each class under dent package
    that has a command implementation in atleast one of the platform
    """

    def __init__(self, cls, fname):
        self._cls = cls
        self._fname = fname
        self._header = [PyLines(lines=tokenize(py_header % self._cls._yfile))]
        self._imports = []
        self._classes = []
        self._methods = []

    def generate_code(self):
        args = self._cls.to_dict()
        args['cname_cc'] = camelcase(self._cls.name)
        self._imports.append(PyImport('pytest'))
        self._imports.append(PyImport('TestLibObject', _from='dent_os_testbed.lib.test_lib_object '))
        for impl in self._cls.implemented_by:
            pd_impl = ''
            if 'dentos' in impl.platforms:
                args['pd_impl_cc'] = '%sImpl' % camelcase(impl.name)
                args['pd_impl'] = 'linux'
            elif 'ixnetwork' in impl.platforms:
                args['pd_impl_cc'] = '%sImpl' % camelcase(impl.name)
                args['pd_impl'] = 'ixnetwork'
            elif 'dni' in impl.platforms:
                args['pd_impl_cc'] = '%sImpl' % camelcase(impl.name)
                args['pd_impl'] = 'dni'
            else:
                continue
            self._imports.append(
                PyImport(
                    '%(pd_impl_cc)s ' % args,
                    _from='dent_os_testbed.lib.%(cls_mod_name)s.%(pd_impl)s.'
                    % (args)
                    + impl.name
                    + '_impl ',
                )
            )
        # generate the init routine
        methods = []
        impl_form_cmd = ''
        for obj in self._cls.implemented_by:
            iargs = {
                'cname_cc' : camelcase(obj.name),
                'platforms': obj.platforms,
                }
            impl_form_cmd += py_class_common_impl_form_command % iargs
        args['impl_form_cmd'] = impl_form_cmd
        if self._cls.local:
            args['invoke_command'] = 'rc, output = impl_obj.run_command(device_obj, command=api, params=device[device_name])'
        else:
            args['invoke_command'] = 'rc, output = await device_obj.run_cmd(("sudo " if device_obj.ssh_conn_params.pssh else "") + commands)'
        args['local'] = 'impl' if self._cls.local else 'device'
        run_body = tokenize(py_class_common_run % args),
        methods.append(PyMethod('_run_command',
                                'api, *argv, **kwarg',
                                run_body[0],
                                indent=4, coroutine=True))
        for api in self._cls.apis:
            args['cls_api'] = api
            params = ''
            platforms = ''
            cmd_desc = ''
            for impl in self._cls.implemented_by:
                platforms = impl.platforms
                for cmd in impl.commands:
                    if api in cmd.apis:
                        cmd_desc = cmd.desc
                        for p in cmd.params:
                            if not isinstance(p, str):
                                params += "                '%s':'%s',\n" % (p.name, p.type)
                            else:
                                params += "                '%s':'undefined',\n" % (p)
                        break
            args['params'] = params[:-1]
            args['platforms'] = platforms
            args['cmd_desc'] = cmd_desc
            run_body = tokenize(py_class_common_run_api % args),
            methods.append(PyMethod(api.lower(),
                                    '*argv, **kwarg',
                                    run_body[0],
                                    indent=4,coroutine=True))
        # discard other accessors
        self._classes = [
            PyClass(camelcase(self._cls.name),
                    desc=[PyLines(lines=tokenize(self._cls.desc, indent=8))],
                    parent='TestLibObject',
                    methods=methods)
        ]

    def write_file(self):
        p = PyFile(self._header, self._imports, self._classes, self._methods)
        p.write(self._fname)


class TestCmdPyObject(object):
    def __init__(self, cls, fname):
        self._cls = cls
        self._fname = fname
        self._header = [PyLines(lines=tokenize(py_header % self._cls._yfile))]
        self._imports = []
        self._classes = []
        self._methods = []

    def generate_code(self):
        self._imports.append(PyImport('TestLibObject', _from='dent_os_testbed.lib.test_lib_object '))
        args = self._cls.to_dict()
        args['cname_cc'] = camelcase(self._cls.name)
        methods = []
        # add format_cmd method
        format_entries = ''
        run_entries = ''
        parse_entries = ''
        need_run = False
        for cmd in self._cls.commands:
            # add the methods to handle the generation
            cargs = cmd.to_dict()
            format_cmd_body = tokenize(py_class_common_format_cmd % cargs)
            methods.append(
                PyMethod(
                    'format_%s' % cmd.name, 'self, command, *argv, **kwarg', format_cmd_body, indent=4,
                )
            )
            if self._cls.implements.local:
                need_run = True
                run_cmd_body = tokenize(py_class_common_run_cmd % cargs)
                methods.append(
                    PyMethod(
                        'run_%s' % cmd.name, 'self, device, command, *argv, **kwarg', run_cmd_body, indent=4,
                    )
                )
            parse_cmd_body = tokenize(py_class_common_parse_cmd % cargs)
            methods.append(
                PyMethod(
                    'parse_%s' % cmd.name, 'self, command, output, *argv, **kwarg', parse_cmd_body, indent=4,
                )
            )
            args['cmds'] = cmd.apis
            args['cmd'] = cmd.name
            format_entries += py_class_common_format_cmd_case % (args)
            run_entries += py_class_common_run_cmd_case % (args)
            parse_entries += py_class_common_parse_cmd_case % (args)
        args['format_entries'] = format_entries
        args['run_entries'] = run_entries if need_run else ''
        args['parse_entries'] = parse_entries
        format_cmd_body = tokenize(py_class_common_format_cmds % args)
        methods.append(
            PyMethod('format_command', 'self, command, *argv, **kwarg', format_cmd_body, indent=4)
        )
        if need_run:
            run_cmd_body = tokenize(py_class_common_run_cmds % args)
            methods.append(
                PyMethod('run_command', 'self, device_obj, command, *argv, **kwarg', run_cmd_body, indent=4)
        )

        parse_cmd_body = tokenize(py_class_common_parse_cmds % args)
        methods.append(
            PyMethod('parse_output', 'self, command, output, *argv, **kwarg', parse_cmd_body, indent=4)
        )
        self._classes.append(
            PyClass(camelcase(self._cls.name),
                    desc=[PyLines(lines=tokenize(self._cls.desc, indent=8))],
                    parent='TestLibObject',
                    methods=methods)
        )

    def write_file(self):
        p = PyFile(self._header, self._imports, self._classes, self._methods)
        p.write(self._fname)


class TestCmdImplPyObject(object):
    def __init__(self, cls, fname, platform):
        self._cls = cls
        self._fname = fname
        self._platform = platform
        self._header = []
        self._imports = []
        self._classes = []
        self._methods = []

    def generate_code(self):
        args = self._cls.to_dict()
        args['cname_cc'] = camelcase(self._cls.name)
        self._imports.append(
            PyImport(
                '%(cname_cc)s ' % args,
                _from='dent_os_testbed.lib.%s.%s.'
                % (self._cls._mod.name, self._platform)
                + self._cls.name
                + ' ',
            )
        )
        methods = []
        # add format_cmd method
        entries = ''
        for cmd in self._cls.commands:
            # add the methods to handle the generation
            cargs = cmd.to_dict()
            format_cmd_body = tokenize(py_impl_class_common_format_cmd % cargs)
            methods.append(
                PyMethod(
                    'format_%s' % cmd.name, 'self, command, *argv, **kwarg', format_cmd_body, indent=4,
                )
            )
            if self._cls.implements.local:
                run_cmd_body = tokenize(py_impl_class_common_run_cmd % cargs)
                methods.append(
                    PyMethod(
                        'run_%s' % cmd.name, 'self, device, command, *argv, **kwarg', run_cmd_body, indent=4,
                    )
                )

            parse_cmd_body = tokenize(py_impl_class_common_parse_cmd % cargs)
            methods.append(
                PyMethod(
                    'parse_%s' % cmd.name, 'self, command, output, *argv, **kwarg', format_cmd_body, indent=4,
                )
            )
        self._classes.append(
            PyClass(
                camelcase(self._cls.name + 'Impl'),
                desc=[PyLines(lines=tokenize(self._cls.desc, indent=8))],
                parent=camelcase(self._cls.name),
                methods=methods,
            )
        )

    def write_file(self):
        p = PyFile(self._header, self._imports, self._classes, self._methods)
        p.write(self._fname)


class TestPlugin(SamplePlugin):
    def __init__(self, name):
        self.name = name

    def generate_code(self, dbs, odir):
        """
        1. select the netprof package.
        2. iterate through all the modules and classes
        3. If the classs has one implementation in the platform then generate the py file.
        4. select the linux package
        5. iterate through all the modules and classes
        6. generate the routine to handle format command and parse output calls from dent py files.
        7. generate the impl.py.gen template file
        """
        print('Generating Test')
        # create the directory
        tdir = os.path.join(odir, 'src/dent_os_testbed/lib/')
        if not os.path.exists(tdir):
            os.makedirs(tdir)
        #gi = os.path.join(tdir, ".gitignore")
        #gd = open(gi, "w")
        for mname, m in dbs['dent'].modules.items():
            mdir = os.path.join(tdir, mname)
            for c in m.classes:
                # don't bother generating the py file if there is not event single platform this
                # class is implemented in
                if not c.implemented_by:
                    continue
                if not os.path.exists(mdir):
                    os.mkdir(mdir)
                    fname = os.path.join(mdir, '__init__.py')
                    f = open(fname, 'w')
                    f.close()
                fname = os.path.join(mdir, c.name + '.py')
                o = TestPyObject(c, fname)
                o.generate_code()
                o.write_file()
                #gd.write(f"{mname}/{c.name}.py\n")
        for mname, m in dbs['linux'].modules.items():
            mdir = os.path.join(tdir, mname)
            mdir = os.path.join(mdir, 'linux')
            if not os.path.exists(mdir):
                os.mkdir(mdir)
                fname = os.path.join(mdir, '__init__.py')
                f = open(fname, 'w')
                f.close()
            for c in m.classes:
                fname = os.path.join(mdir, c.name + '.py')
                o = TestCmdPyObject(c, fname)
                o.generate_code()
                o.write_file()
                #gd.write(f"{mname}/linux/{c.name}.py\n")
                fname = os.path.join(mdir, c.name + '_impl.py')
                if os.path.exists(fname):
                    fname += '.gen'
                o = TestCmdImplPyObject(c, fname, 'linux')
                o.generate_code()
                o.write_file()

        for mname, m in dbs['traffic'].modules.items():
            mdir = os.path.join(tdir, mname)
            mdir = os.path.join(mdir, 'ixnetwork')
            if not os.path.exists(mdir):
                os.mkdir(mdir)
                fname = os.path.join(mdir, '__init__.py')
                f = open(fname, 'w')
                f.close()
            for c in m.classes:
                fname = os.path.join(mdir, c.name + '.py')
                o = TestCmdPyObject(c, fname)
                o.generate_code()
                o.write_file()
                #gd.write(f"{mname}/ixnetwork/{c.name}.py\n")
                fname = os.path.join(mdir, c.name + '_impl.py')
                if os.path.exists(fname):
                    fname += '.gen'
                o = TestCmdImplPyObject(c, fname, 'ixnetwork')
                o.generate_code()
                o.write_file()

        for mname, m in dbs['poe_tester'].modules.items():
            mdir = os.path.join(tdir, mname)
            mdir = os.path.join(mdir, 'dni')
            if not os.path.exists(mdir):
                os.mkdir(mdir)
                fname = os.path.join(mdir, '__init__.py')
                f = open(fname, 'w')
                f.close()
            for c in m.classes:
                fname = os.path.join(mdir, c.name + '.py')
                o = TestCmdPyObject(c, fname)
                o.generate_code()
                o.write_file()
                #gd.write(f"{mname}/ixnetwork/{c.name}.py\n")
                fname = os.path.join(mdir, c.name + '_impl.py')
                if os.path.exists(fname):
                    fname += '.gen'
                o = TestCmdImplPyObject(c, fname, 'dni')
                o.generate_code()
                o.write_file()
        #gd.close()


class TestCodePyObject(object):
    def __init__(self, cls, fname):
        self._cls = cls
        self._fname = fname
        self._header = [PyLines(lines=tokenize(py_header % self._cls._yfile))]
        self._imports = []
        self._classes = []
        self._methods = []

    def get_random_value(self, mbr):
        if isinstance(mbr, str):
            return ''
        if mbr.type == 'string':
            return '\''+''.join(random.choice(string.ascii_lowercase) for i in range(8)) + '\''
        if mbr.type == 'string_list':
            ret = []
            for n in range(random.randint(1, 10)):
                ret.append(''.join(random.choice(string.ascii_lowercase) for i in range(8)))
            return ret
        if mbr.type == 'int':
            return str(random.randint(100, 10000))
        if mbr.type == 'float':
            return str(random.random())
        if mbr.type == 'bool':
            return 'True' if random.randint(0, 1) else 'False'
        if mbr.type == 'ip_addr_t':
            return '\''+'.'.join(map(str, (random.randint(0, 255) for _ in range(4)))) + '\''
        if mbr.type == 'mac_t':
            return '\''+ ':'.join(map(str, ('%02x' % random.randint(0, 255) for _ in range(6)))) + '\''
        return '\'\''

    def generate_code(self):
        args = self._cls.to_dict()
        args['cname_cc'] = camelcase(self._cls.name)
        self._imports.append(PyImport('asyncio'))
        self._imports.append(PyImport('TestDevice', _from='.utils '))
        self._imports.append(
            PyImport(
                '%(cname_cc)s ' % args,
                _from='dent_os_testbed.lib.%s.'
                % (self._cls._mod.name)
                + self._cls.name
                + ' ',
            )
        )
        for api in self._cls.apis:
            args['api'] = api
            test_body_call = ''
            for impl in self._cls.implemented_by:
                for cmd in impl.commands:
                    if api not in cmd.apis: continue
                    args['params1'] = ''
                    args['params2'] = ''
                    for m in cmd.params:
                        if isinstance(m, str):
                            continue
                        # ignore if its readonly
                        if m.readonly:
                            continue
                        args['params1'] += "        '%s':%s,\n" % (m.name, self.get_random_value(m))
                        args['params2'] += "        '%s':%s,\n" % (m.name, self.get_random_value(m))
                    test_body_call += py_test_code_two_cmd_template_call % args
                    test_body_call += py_test_code_two_dev_template_call % args
                    break
            args['platform'] = self._cls.implemented_by[0].platforms[0]
            args['cases'] = test_body_call
            test_body = tokenize(py_test_code_template % args)
            self._methods.append(
                PyMethod('test_that_%(cls_name)s_%(api)s' % args, 'capfd', test_body)
            )

    def write_file(self):
        p = PyFile(self._header, self._imports, self._classes, self._methods)
        p.write(self._fname)


class TestCodePlugin(SamplePlugin):
    def __init__(self, name):
        self.name = name

    def generate_code(self, dbs, odir):
        """
        1. iterate through all modules under dent package
        2. generate unit test code to
          2.1 invoke the api with no params on a single device
          2.2 invoke the api with two calls on a single device
          2.3 invoke the api with one call on two devices.
        3. expect the command to be formed and the return code alteast.
        """
        print('Generating Test Code')
        # create the directory
        tdir = os.path.join(odir, 'test/')
        if not os.path.exists(tdir):
            os.makedirs(tdir)
        #gi = os.path.join(tdir, ".gitignore")
        #gd = open(gi, "w")
        for mname, m in dbs['dent'].modules.items():
            for c in m.classes:
                # don't bother generating the py file if there is not event single platform this
                # class is implemented in
                if not c.implemented_by:
                    continue
                fname = os.path.join(tdir, dent_test_prefix + c.name + '.py')
                #gd.write(dent_test_prefix + c.name + ".py\n")
                if os.path.exists(fname):
                    continue
                o = TestCodePyObject(c, fname)
                o.generate_code()
                o.write_file()
        #gd.close()
