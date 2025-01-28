
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

from copy import deepcopy

from leaf_common.config.config_filter import ConfigFilter


class AbstractCommonDefsConfigFilter(ConfigFilter):
    """
    An abstract ConfigFilter implementation that takes a agent tool registry config
    that may or may not contain a particular set commondefs definitions
    and does an calls an abstract make_replacements() method for appropriate
    values.
    """

    def __init__(self, commondefs_key: str, replacements: Dict[str, Any] = None):
        """
        Constructor

        :param commondefs_key: The string key in the commondefs section
                that contains the replacement dictionary.
        :param replacements: An initial replacements dictionary to start out with
                whose (copied) contents will be updated with commondefs definitions
                in the basis_config during the filter_config() entry point.
                Default is None, indicating everything needed comes from the config.
        """
        self.commondefs_key: str = commondefs_key
        self.starting_replacements: Dict[str, Any] = replacements
        if replacements is None:
            self.starting_replacements = {}

    def filter_config(self, basis_config: Dict[str, Any]) -> Dict[str, Any]:
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
        if basis_config is None or not basis_config:    # Empty dictionaries evaluate to False
            # Nothing to modify
            return basis_config

        # Start our replacement dictionary with what was passed into the constructor
        replacements: Dict[str, Any] = deepcopy(self.starting_replacements)

        # Look for something to replace
        commondefs: Dict[str, Any] = {}
        commondefs = basis_config.get("commondefs", commondefs)
        if commondefs:          # Empty dictionaries evaluate to False
            new_replacements: Dict[str, Any] = {}
            new_replacements = deepcopy(commondefs.get(self.commondefs_key, new_replacements))
            replacements.update(new_replacements)

        if not replacements:               # Empty dictionaries evaluate to False
            # No modifications to make
            return basis_config

        # Start out with a copy of the basis.  Leave the input alone.
        new_config: Dict[str, Any] = deepcopy(basis_config)

        # First do replacements among commondef dictionaries themselves
        # Note: These cannot have cycles.
        replacements = self.filter_one_dict(replacements, replacements)

        # Next do replacements among all tools dicts
        tools: List[Dict[str, Any]] = basis_config.get("tools")
        new_config["tools"] = self.filter_one_list(tools, replacements)

        return new_config

    def filter_one_dict(self, source: Dict[str, Any], replacements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs the filter on the values of a dictionary

        :param source: The dictionary to filter
        :param replacements: A dictionary of string keys to their replacements
        :return: A new dictionary whose value are (maybe) replaced per the
                 replacements dictionary
        """

        new_dict = deepcopy(source)
        for key, value in source.items():

            replacement_value: Any = None

            if isinstance(value, Dict):
                # We have a dictionary value. Recurse.
                replacement_value = self.filter_one_dict(value, replacements)
            elif isinstance(value, List):
                replacement_value = self.filter_one_list(value, replacements)
            else:
                replacement_value = self.make_replacements(value, replacements)

            if replacement_value is not None:
                new_dict[key] = replacement_value

        return new_dict

    def filter_one_list(self, source: List[Any], replacements: Dict[str, Any]) -> List[Any]:
        """
        Performs the filter on the elements of a list

        :param source: The list to filter
        :param replacements: A dictionary of string keys to their replacements
        :return: A new List whose components are (maybe) replaced per the
                 replacements dictionary
        """

        new_list: List[Any] = []
        for component in source:

            replacement_value: Any = component

            if isinstance(component, Dict):
                replacement_value = self.filter_one_dict(component, replacements)
            elif isinstance(component, List):
                replacement_value = self.filter_one_list(component, replacements)
            else:
                replacement_value = self.make_replacements(component, replacements)

            new_list.append(replacement_value)

        return new_list

    def make_replacements(self, source_value: Any, replacements: Dict[str, Any]) -> Any:
        """
        Make replacements per the keys and values in the replacements dictionary

        :param source_value: The value to potentially do replacements on
        :param replacements: A dictionary of string keys to their replacements
        :return: A potentially new value if some key in the replacements dictionary
                is found to trigger a replacement, otherwise, the same source_value
                that came in.
        """
        raise NotImplementedError
