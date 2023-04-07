"""plugin.py

TestSuiteLib plugin to generate test suite tests based on the templates listed in model/test.

"""


import fnmatch
import imp
import os
import json
import inspect
from gen.lib.database import camelcase
from gen.lib.python.pylib import PyFile, PyImport, PyLines
from gen.lib.sample_plugin import SamplePlugin
from gen.plugins.test_suite.template import py_ts_header


class TestSuitePyObject(object):
    """
    Generates the Test suite file contianing all the tests.
    """
    def __init__(self, test, fname):
        self._test = test
        self._fname = fname
        self._header = [PyLines(lines=tokenize(py_ts_header % self._test._yfile))]
        self._imports = []
        self._classes = []
        self._methods = []

    def generate_code(self):
        args = self._test.to_dict()
        self._imports.append(PyImport('pytest'))
        self._imports.append(PyImport('time'))
        self._imports.append(PyImport('re'))
        self._imports.append(PyImport('TestCaseSetup', _from='dent_os_testbed.utils.decorators '))
        imported = {}
        classes = ''
        for tc in self._test.test_cases:
            targs = {**args, **tc.to_dict()}
            if tc.cls:
                targs = {**targs, **tc.cls.to_dict()}
                # if there is an class then do an import if not done.
                if tc.cls.implemented_by and tc.cls.name not in imported:
                    self._imports.append(
                        PyImport(
                            '%(cls_cc_name)s ' % targs,
                            _from='dent_os_testbed.lib.%s.'
                            % (tc.cls._mod.name)
                            + tc.cls.name
                            + ' ',
                        )
                    )
                    imported[tc.cls.name] = True
            if tc.template not in imported:
                self._imports.append(
                    PyImport(
                        '%sBase, %sMeta ' % (tc.template, tc.template),
                        _from='dent_os_testbed.test.lib.%s ' % (tc.template)
                    )
                )
                imported[tc.template] = True
            if tc.args:
                tc_args = json.loads(tc.args)
                methods = []
                for k in tc_args.keys():
                    methods.append(
                        PyMethod(k, 'obj=None', ['return '+tc_args[k]], indent=4)
                    )
                cls = camelcase(tc.cls.name)+tc.template+'Meta'
                self._classes.append(
                    PyClass(cls,
                            desc=[PyLines(lines=[])],
                            parent=('%sMeta' % tc.template),
                            methods=methods)
                )
                self._classes.append(
                    PyClass(camelcase(tc.cls.name)+tc.template,
                            desc=[PyLines(lines=[])],
                            parent=('%sBase' % tc.template),
                            methods=[PyLines(
                                lines=['    meta='+
                                       camelcase(tc.cls.name)+
                                       tc.template+
                                       'Meta'])]
                    )
                )
                classes += camelcase(tc.cls.name)+tc.template + ','
            #self._methods.append(PyLines(lines=tokenize(self._templates[tc.template]._data%targs)))
        self._methods.append(PyLines(lines=['@pytest.fixture(params=[%s])' % classes]))
        self._methods.append(PyMethod(self._test.name+'_class', 'request',  ['return request.param']))
        self._methods.append(PyLines(lines=['@pytest.mark.asyncio']))
        self._methods.append(PyMethod('test_'+self._test.name, 'testbed, '+self._test.name+'_class', ['await ' + self._test.name+'_class'+'().run_test(testbed)'], coroutine=True))
        self._imports.append(PyLines(lines=['pytestmark = pytest.mark.suite_basic_trigger']))
    def write_file(self):
        p = PyFile(self._header, self._imports, self._classes, self._methods)
        p.write(self._fname)


class TestSuitePlugin(SamplePlugin):
    def __init__(self, name):
        self.name = name

    def generate_code(self, dbs, odir):
        """
        1. select the test package.
        2. iterate through all the modules and tests
        4. generate the test cases for each test case under it.
        """
        print('Generating Test Suite')

        # create the directory
        tdir = os.path.join(odir, 'src/dent_os_testbed/test/test_suite/generated')
        #gi = os.path.join(tdir, ".gitignore")
        #gd = open(gi, "w")
        if not os.path.exists(tdir):
            os.makedirs(tdir)
            fname = os.path.join(tdir, '__init__.py')
            f = open(fname, 'w')
            f.write("__import__(\"pkg_resources\").declare_namespace(__name__)")
            f.close()
        for mname, m in dbs['test'].modules.items():
            for t in m.tests:
                fname = os.path.join(tdir, 'test_' + t.name + '.py')
                o = TestSuitePyObject(t, fname)
                o.generate_code()
                o.write_file()
                #gd.write(f"test_{t.name}.py\n")
        #gd.close()
