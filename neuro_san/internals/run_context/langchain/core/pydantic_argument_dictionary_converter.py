
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
from __future__ import annotations

from typing import Any
from typing import Dict

from pydantic import BaseModel

from leaf_common.serialization.interface.dictionary_converter import DictionaryConverter


class PydanticArgumentDictionaryConverter(DictionaryConverter):
    """
    DictionaryConverter implementation which can convert a
    dynamically created pydantic object to a dictionary for use
    in passing arguments around.
    """

    def to_dict(self, obj: BaseModel) -> Dict[str, Any]:
        """
        :param obj: The object to be converted into a dictionary
        :return: A data-only dictionary that represents all the data for
                the given object, either in primitives
                (booleans, ints, floats, strings), arrays, or dictionaries.
                If obj is None, then the returned dictionary should also be
                None.  If obj is not the correct type, it is also reasonable
                to return None.
        """
        # Do the pydantic conversion to a dict
        base_dict: Dict[str, Any] = dict(obj)

        # Loop through all the keys, converting any other
        # sub-objects that are BaseModels to dictionaries as well.
        new_dict: Dict[str, Any] = {}
        for key, value in base_dict.items():
            new_value: Any = value
            if isinstance(value, Dict) or self.is_pydantic_object(value):
                new_value = self.to_dict(value)
            # Note: We might need to go through list components, too.
            new_dict[key] = new_value

        return new_dict

    def from_dict(self, obj_dict: Dict[str, Any]) -> BaseModel:
        """
        :param obj_dict: The data-only dictionary to be converted into an object
        :return: An object instance created from the given dictionary.
                If obj_dict is None, the returned object should also be None.
                If obj_dict is not the correct type, it is also reasonable
                to return None.
        """
        # At this point we are not going back to BaseModel objects
        raise NotImplementedError

    def is_pydantic_object(self, value: Any) -> bool:
        """
        :param value: the value to test
        :return: True if the object is a pydantic object. False otherwise.
        """
        return hasattr(value, "parse_obj") and callable(value.parse_obj)
