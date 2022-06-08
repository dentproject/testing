"""pylib.py

set of routines used to generate a python file.
"""


class PyLine(object):
    def __init__(self, line=""):
        self._line = line

    def write_line(self, f, line):
        f.write(line + "\n")


class PyLines(PyLine):
    def __init__(self, lines=[]):
        self._lines = lines

    def indent(self, _indent):
        self._lines = [(" " * _indent + l) for l in self._lines]

    def write(self, f):
        for l in self._lines:
            self.write_line(f, l)


class PyImport(PyLines):
    def __init__(self, _import, _from=None, _as=None, indent=0):
        self._lines = []
        _line = ("from " + _from) if _from else ""
        _line += "import " + _import
        _line += "as " + _as if _as else ""
        self._lines.append(_line)
        self.indent(indent)


class PyMethod(PyLines):
    def __init__(self, name, params, body, indent=0, coroutine=False):
        self._lines = ["def %s(%s):" % (name, params)]
        if coroutine: self._lines[0] = "async " + self._lines[0]
        for l in body:
            self._lines.append("    " + l)
        self.indent(indent)

class PyClass(PyLines):
    def __init__(self, name, parent="object", desc=[], static=[], methods=[], indent=0):
        self._lines = ["class %s(%s):" % (name, parent)]
        self._lines.append("    \"\"\"")
        for d in desc:
            self._lines += d._lines
        self._lines.append("    \"\"\"")
        for s in static:
            self._lines += s._lines
        for m in methods:
            self._lines += m._lines
        self.indent(indent)


class PyFile(object):
    def __init__(self, header, imports, classes, methods):
        self._header = header
        self._imports = imports
        self._classes = classes
        self._methods = methods

    def write(self, fname):
        f = open(fname, "w", encoding="utf-8")
        for i in self._header:
            i.write(f)
        for i in self._imports:
            i.write(f)
        for i in self._classes:
            i.write(f)
        for i in self._methods:
            i.write(f)
        f.close()
