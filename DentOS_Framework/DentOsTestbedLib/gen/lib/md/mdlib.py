"""mdlib.py

set of routines used to generate a md file.
"""


class MdLine(object):
    def __init__(self, line=""):
        self._line = line

    def write_line(self, f, line):
        f.write(line + "\n")


class MdLines(MdLine):
    def __init__(self, lines=[]):
        self._lines = lines

    def indent(self, _indent):
        self._lines = [(" " * _indent + l) for l in self._lines]

    def write(self, f):
        for l in self._lines:
            self.write_line(f, l)


class MdFile(object):
    def __init__(self, header, body, trailer):
        self._header = header
        self._body = body
        self._trailer = trailer

    def write(self, fname):
        f = open(fname, "w", encoding="utf-8")
        for i in self._header:
            i.write(f)
        for i in self._body:
            i.write(f)
        for i in self._trailer:
            i.write(f)
        f.close()
