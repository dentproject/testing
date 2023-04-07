"""code_generate.py

Code generation module to read yaml models and feed it to dynamic plugins
"""

import fnmatch
import imp
import inspect
import os

import yaml
from pykwalify.core import Core
from pykwalify.errors import PyKwalifyException

from gen.lib.database import Package
from gen.lib.sample_plugin import SamplePlugin


def load_yaml(yaml_dir):
    """
    1. recursively walk the directories looking for yaml files.
    2. top level directory represents package
    3. Keep constructing pkg->module->classes,types,commands etc
    """
    content = dict()
    schema_file = os.path.join(yaml_dir, 'schema.yaml')
    for root, dirnames, filenames in os.walk(yaml_dir):
        for filename in fnmatch.filter(filenames, '*.yaml'):
            if filename == 'schema.yaml':
                continue
            fname = os.path.join(root, filename)
            with open(fname, 'r', encoding='utf-8') as fp:
                ydata = yaml.safe_load(fp)

            try:
                c = Core(source_data=ydata, schema_files=[schema_file])
                c.validate(raise_exception=True)
            except PyKwalifyException as e:
                raise e

            pname = root[len(yaml_dir) :].split('/')[0]
            print (fname)
            if pname not in content:
                content[pname] = Package(pname, ydata, fname, content)
            else:
                content[pname].append_to_pkg(ydata, fname)

    for c, v in content.items():
        v.validate()

    for c, v in content.items():
        v.post_validate()

    return content


def load_plugins(plugin_dir):
    """
    1. Look for plugin.py under plugin_dir
    2. instatiate the classes that have inherited SamplePlugin
    """
    content = {}
    for root, dirnames, filenames in os.walk(plugin_dir):
        for filename in fnmatch.filter(filenames, 'plugin.py'):
            fname = os.path.join(root, filename)
            module = imp.load_source('plugin', fname)
            for name, cls in inspect.getmembers(module):
                if name == 'SamplePlugin':
                    continue
                if (
                    inspect.isclass(cls)
                    and issubclass(cls, SamplePlugin)
                    and name not in content.keys()
                ):
                    print('Loading Plugin ' + name)
                    content[name] = cls(name)
    return content


def main(
    plugin_dir='./plugins/',
    yaml_dir='./model/',
    yang_dir='./model/',
    output_dir='/tmp/codegen/',
):
    """
    1. Load the plugins.
    2. Load the model from yaml fils
    3. Invoke the plugin to generate the repective code.
    """
    plugins = load_plugins(plugin_dir)
    dbs = load_yaml(yaml_dir)
    for _, p in plugins.items():
        p.generate_code(dbs, output_dir)


if __name__ == '__main__':
    main()
