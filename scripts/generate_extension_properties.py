#!/usr/bin/env python3
"""
This script dynamically generates two python modules each containing one class. One is inherited by LDAP and the other
by LDAPObject. They contain a ``@property`` for each extension defined in
:attr:`.extensible.Extensible.AVAILABLE_EXTENSIONS` which defines an extension class for the appropriate parent
class.
"""
from laurelin.ldap.extensible import Extensible, ExtensibleClass, CLASS_EXTENSION_FMT
from importlib import import_module
from inspect import stack
from os.path import dirname, abspath, join as path_join
import jinja2

EXTENSION_TEMPLATE = jinja2.Template('''"""Automatically generated by scripts/generate_extension_properties.py

**DO NOT MODIFY - CHANGES WILL BE OVERWRITTEN**
"""

from .base import {{ BASE }}


class {{ EXTENDS }}Extensions({{ BASE }}):
{% for name, extinfo in AVAILABLE_EXTENSIONS %}
    @property
    def {{ name }}(self):
        """{{ extinfo['docstring'] }}

        :rtype: {{ extinfo['module'] }}.Laurelin{{ EXTENDS }}Extension
        """
        return self._get_extension_instance('{{ name }}')
{% else %}
    pass
{% endfor %}
''')

BASE_DIR = path_join(dirname(abspath(stack()[0][1])), '..')


def _render_extensions_module(**kwds):
    extends_classname = kwds.get('EXTENDS', 'laurelin')

    # render the template into a module
    filename = '{0}_extensions.py'.format(extends_classname.lower())
    with open(path_join(BASE_DIR, 'laurelin', 'ldap', 'extensible', filename), 'w') as f:
        f.write(EXTENSION_TEMPLATE.render(**kwds))
        print('Generated new {0}'.format(filename))


def _sorted_dict_items(dct):
    keys = list(dct.keys())
    keys.sort()
    lst = []
    for key in keys:
        lst.append((key, dct[key]))
    return lst


def main():
    # Render main extensions module giving access to all LaurelinExtension classes

    ext_list = _sorted_dict_items(Extensible.AVAILABLE_EXTENSIONS)
    _render_extensions_module(AVAILABLE_EXTENSIONS=ext_list,
                              BASE='ExtensionsBase')

    # Render class extension modules

    ext_classes = []
    for clsname in ExtensibleClass.EXTENSIBLE_CLASSES:
        ext_classes.append((clsname, {}))

    for name, extinfo in Extensible.AVAILABLE_EXTENSIONS.items():
        mod = import_module(extinfo['module'])
        for classname, ext_dict in ext_classes:
            classname = CLASS_EXTENSION_FMT.format(classname)
            try:
                # ensure the required class exists in the module
                getattr(mod, classname)
                # if it does, store it in the appropriate dict
                ext_dict[name] = extinfo
            except AttributeError:
                # do nothing if it doesn't define the class
                pass

    for extends_classname, available_extensions in ext_classes:
        # make a sorted list from the dict so we generate a deterministic file
        ext_list = _sorted_dict_items(available_extensions)

        _render_extensions_module(EXTENDS=extends_classname,
                                  AVAILABLE_EXTENSIONS=ext_list,
                                  BASE='ExtensibleClass')


if __name__ == '__main__':
    main()
