"""Automatically generated by scripts/generate_extension_properties.py

**DO NOT MODIFY - CHANGES WILL BE OVERWRITTEN**
"""

from .base import ExtensionsBase


class Extensions(ExtensionsBase):

    @property
    def descattrs(self):
        """The built-in description attributes extension

        :rtype: laurelin.extensions.descattrs.LaurelinExtension
        """
        return self._get_extension_instance('descattrs')

    @property
    def netgroups(self):
        """The built-in NIS netgroups extension

        :rtype: laurelin.extensions.netgroups.LaurelinExtension
        """
        return self._get_extension_instance('netgroups')
