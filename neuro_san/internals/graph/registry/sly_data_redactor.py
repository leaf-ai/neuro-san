
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
from typing import List

from leaf_common.config.config_filter import ConfigFilter
from leaf_common.parsers.dictionary_extractor import DictionaryExtractor


class SlyDataRedactor(ConfigFilter):
    """
    An implementation of the ConfigFilter interface which redacts sly data
    based on calling-agent specs.
    """

    def __init__(self, calling_agent_tool_spec: Dict[str, Any],
                 config_keys: List[str] = []):
        """
        Constructor

        :param calling_agent_tool_spec: The dictionary describing the JSON agent tool
                            that is providing the sly_data.
        :param keys: A list of config keys in reverse precedence order.
        """
        self.agent_tool_spec: Dict[str, Any] = calling_agent_tool_spec
        self.config_keys: List[str] = config_keys

    def filter_config(self, basis_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param basis_config: Source of the sly_data to redact.
        :return: A new sly_data dictionary with proper redactions per the "allow.sly_data"
                dictionary on the agent spec.  If no such key exists, then no sly_data
                gets through to the agent to be called.
        """
        empty: Dict[str, Any] = {}

        extractor = DictionaryExtractor(self.agent_tool_spec)

        # Find the right dictionary given the configured config_keys.
        allow_dict: Dict[str, Any] = empty
        for config_key in self.config_keys:
            allow_dict = extractor.get(config_key, allow_dict)

        # Recall empty dictionaries evaluate to False (as well as boolean values)
        if not bool(allow_dict):
            # By default we don't let anything through
            return empty

        if isinstance(allow_dict, bool) and bool(allow_dict):
            # The value is a simple True, so let everything through.
            return basis_config

        if not bool(basis_config) or not isinstance(basis_config, Dict):
            # There is no dictionary content, so nothing to redact
            return empty

        # Got rid of all the easy cases.
        # Now leaf through the keys of the dictionaries.
        # For now, just do top-level keys. Can get more complicated later if need be.
        redacted: Dict[str, Any] = {}
        for source_key, dest_key in allow_dict.items():

            source_value: Any = basis_config.get(source_key)
            if source_value is None:
                # We have an allowance, but no data, so nothing to do for this key.
                continue

            if isinstance(dest_key, str):
                # Translate the key
                redacted[dest_key] = source_value
            elif isinstance(dest_key, bool) and bool(dest_key):
                # Use the same key and the same value in the explicit allow
                redacted[source_key] = source_value

        return redacted
