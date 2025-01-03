
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT
from typing import Any
from typing import Dict

from neuro_san.internals.graph.registry.abstract_common_defs_config_filter \
    import AbstractCommonDefsConfigFilter


class StringCommonDefsConfigFilter(AbstractCommonDefsConfigFilter):
    """
    An AbstractCommonDefsConfigFilter implementation that takes a
    agent tool registry config that may or may not contain commondefs
    definitions for strings to substitute in by key.

    For example: Say in the config there is a top-level definition:

        "commondefs": {
            "replacement_strings": {
                "foo": "bar"
            }
        }

    This ConfigFilter implementation will replace any string containing
    the string value "{foo}" with the full string substitution "bar".
    """

    def __init__(self, replacements: Dict[str, Any] = None):
        """
        Constructor

        :param replacements: An initial replacements dictionary to start out with
                whose (copied) contents will be updated with commondefs definitions
                in the basis_config during the filter_config() entry point.
                Default is None, indicating everything needed comes from the config.
        """
        super().__init__("replacement_strings", replacements)

    def make_replacements(self, source_value: Any, replacements: Dict[str, Any]) -> Any:
        """
        Make replacements per the keys and values in the replacements dictionary

        :param source_value: The value to potentially do replacements on
        :param replacements: A dictionary of string keys to their replacements
        :return: A potentially new value if some key in the replacements dictionary
                is found to trigger a replacement, otherwise, the same source_value
                that came in.
        """

        if not isinstance(source_value, str):
            # We only modify strings in this implementation.
            # Let everything else go through unadulterated.
            return source_value

        replacement_value: str = source_value

        for search, replace in replacements.items():

            if replace is None or len(replace) == 0:
                # Nothing in the dicitonary of replacements.
                # Leave the string as-is.
                # Move along. Nothing to see here.
                continue

            if not isinstance(replace, str) or not isinstance(search, str):
                # Unclear what the user is getting at. Skip.
                continue

            if search not in replacement_value:
                # Don't need to worry about this key
                continue

            # We want to replace any instance of "{<search>}" in a string
            # with the replace value.  In order to preserve the curly braces
            # in an f-string, we need to double them.
            replacement_value = replacement_value.replace(f"{{{search}}}", replace)

        return replacement_value
