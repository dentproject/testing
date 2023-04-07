"""plugin.py

Discovery plugin generates documentation
"""

import os

import random
import string
from gen.lib.sample_plugin import SamplePlugin
from gen.lib.md.mdlib import MdFile, MdLines
from gen.plugins.doc.template import (
    md_header,
    md_apis,
    md_mbr_hdr,
    md_mbr_entry,
    md_mod_hdr,
    md_mod_entry,
    md_sample_call,
)


def tokenize(str, by='\n', indent=0):
    """
    split the lines based on by and return a list of lines by indenting with spaces
    """
    if indent == 0:
        return str.split(by)
    return [ (' '*indent + s) for s in str.split(by) ]


class DocsMdObject(object):
    def __init__(self, pkg, fname):
        self._fname = fname
        self._pkg = pkg
        self._body = []
        self._tailer = []
    def generate_code(self):
        self._header = [MdLines(lines=tokenize('# DENT API Documentation'))]
        self._body.append(MdLines(lines=tokenize(md_mod_hdr)))
        for mname, mod in self._pkg.modules.items():
            margs = mod.to_dict()
            margs['mod_desc'] = margs['mod_desc'].replace('|','\|').replace('\n','')
            classes = ''
            for c in mod.classes:
                if not c.implemented_by:
                    continue
                cargs = c.to_dict()
                classes += f'[{c.name}]({c.name}.md) <br/>'
            if not classes: continue
            margs['classes'] = classes
            self._body.append(MdLines(lines=tokenize(md_mod_entry%margs)))
    def write_file(self):
        p = MdFile(self._header, self._body, self._tailer)
        p.write(self._fname)


class DocMdObject(object):
    def __init__(self, cls, fname):
        self._fname = fname
        self._cls = cls
        self._body = []
        self._tailer = []
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
            return '\''+ ':'.join(map(str, ('%02x'%random.randint(0, 255) for _ in range(6)))) + '\''
        return '\'\''
    def generate_code(self):
        args = self._cls.to_dict()
        args['cname_cc'] = camelcase(self._cls.name)
        self._header = [MdLines(lines=tokenize(md_header%(args)))]
        self._body.append(MdLines(lines=tokenize(md_mbr_hdr)))
        for mbr in self._cls.members:
            margs = mbr.to_dict()
            margs['cmbr_desc'] = margs['cmbr_desc'].replace('|','\|').replace('\n','')
            self._body.append(MdLines(lines=tokenize(md_mbr_entry%margs)))
        for api in self._cls.apis:
            args['api'] = api
            for impl in self._cls.implemented_by:
                # document dentos for now
                if 'dentos' not in impl.platforms: continue
                for cmd in impl.commands:
                    if api not in cmd.apis: continue
                    args['api_desc'] = cmd.desc
                    args['params'] = ''
                    for m in cmd.params:
                        if isinstance(m, str): continue
                        args['params'] += "                '%s':%s,\n" % (m.name, self.get_random_value(m))
                    args['api_name'] = api
                    args['api_usage'] = md_sample_call%args
                    self._body.append(MdLines(lines=tokenize(md_apis%args)))
    def write_file(self):
        p = MdFile(self._header, self._body, self._tailer)
        p.write(self._fname)


class DocPlugin(SamplePlugin):
    """
    1. generate the document for the modules from top level
    2.
    """
    def __init__(self, name):
        self.name = name

    def generate_code(self, dbs, odir):
        print('Generating Document')
        # create the directory
        tdir = os.path.join(odir, 'doc/')
        if not os.path.exists(tdir):
            os.makedirs(tdir)
        gi = os.path.join(tdir, '.gitignore')
        gd = open(gi, 'w')
        gd.write(f'sdk.md\n')
        fname = os.path.join(tdir, 'sdk.md')
        o = DocsMdObject(dbs['dent'], fname)
        o.generate_code()
        o.write_file()
        for mname, m in dbs['dent'].modules.items():
            for c in m.classes:
                # don't bother generating the py file if there is not event single platform this
                # class is implemented in
                if not c.implemented_by:
                    continue
                fname = os.path.join(tdir, c.name + '.md')
                o = DocMdObject(c, fname)
                o.generate_code()
                o.write_file()
                gd.write(f'{c.name}.md\n')
        gd.close()
