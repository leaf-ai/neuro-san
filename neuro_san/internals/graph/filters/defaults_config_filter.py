
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
"""
See class comment for details
"""

from typing import Any
from typing import Dict
from typing import List

from copy import deepcopy

from leaf_common.config.config_filter import ConfigFilter
from leaf_common.config.dictionary_overlay import DictionaryOverlay
from leaf_common.parsers.dictionary_extractor import DictionaryExtractor


class DefaultsConfigFilter(ConfigFilter):
    """
    ConfigFilter implementation for copying top-level defaults
    into individual agents.
    """

    # A mapping of source keys for defaults at the top level to destination
    # keys on the specific tool where the top-level defaults (if any) should be copied.
    DEFAULTS_MAPPING: Dict[str, str] = {
        # A value of None implies using the source key as the same destination
        # key in the tool as well.
        "llm_config": None,
        "llm_config.verbose": "verbose",
        "verbose": None,
        "max_iterations": None,
        "max_execution_seconds": None,
        "error_formatter": None,
        "error_fragments": None,
    }

    def filter_config(self, basis_config: Dict[str, Any]) \
            -> Dict[str, Any]:
        """
        Filters the given basis config.

        Ideally this would be a Pure Function in that it would not
        modify the caller's arguments so that the caller has a chance
        to decide whether to take any changes returned.

        :param basis_config: The config dictionary to act as the basis
                for filtering
        :return: A config dictionary, potentially modified as per the
                policy encapsulated by the implementation
        """

        if basis_config is None:
            return basis_config

        tools: List[Dict[str, Any]] = basis_config.get("tools")
        if tools is None or len(tools) == 0:
            # Nothing to do. Exit early.
            return basis_config

        # Do a deepcopy of the basis now that we know we are likely to modify it
        result_config: Dict[str, Any] = deepcopy(basis_config)

        # Create a single extractor for the top-level.
        basis_extractor = DictionaryExtractor(basis_config)
        overlayer = DictionaryOverlay()

        # Loop through all the tools making additions.
        tools = result_config.get("tools")
        for tool in tools:
            tool_extractor = DictionaryExtractor(tool)

            # Loop through all the keys in the defaults mapping.
            for basis_source_key, tool_dest_key in self.DEFAULTS_MAPPING.items():

                basis_value = basis_extractor.get(basis_source_key)
                if basis_value is None:
                    # No value to fill out.
                    continue

                # Account for semantics outlined in default_mapping above
                if tool_dest_key is None:
                    tool_dest_key = basis_source_key

                tool_value = tool_extractor.get(tool_dest_key)
                if tool_value is None:
                    # If the tool does not have a value, use the basis_value whole cloth
                    tool[tool_dest_key] = deepcopy(basis_value)

                elif isinstance(tool_value, Dict) and isinstance(basis_value, Dict):
                    # Do a dictionary overlay with basis_value defaults as what is
                    # overrideable. The values of tool_value are favored.
                    tool[tool_dest_key] = overlayer.overlay(basis_value, tool_value)

                # Otherwise, don't touch the value already in the tool.
                # Don't do anything funny with scalars.
                # Don't try to merge lists (semantics are fragile here).

        return result_config
