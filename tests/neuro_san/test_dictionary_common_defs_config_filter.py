
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

import json

from unittest import TestCase

from leaf_common.parsers.dictionary_extractor import DictionaryExtractor
from neuro_san.internals.graph.registry.dictionary_common_defs_config_filter \
    import DictionaryCommonDefsConfigFilter


class TestDictionaryCommonDefsConfigFilter(TestCase):
    """
    Unit tests for DictionaryCommonDefsConfigFilter class.
    """

    def test_assumptions(self):
        """
        Can we construct?
        """
        my_filter = DictionaryCommonDefsConfigFilter()
        self.assertIsNotNone(my_filter)

    def test_no_common_defs(self):
        """
        Tests basic non-operations of the ConfigFilter
        """
        my_filter = DictionaryCommonDefsConfigFilter()

        dict_in: Dict[str, Any] = {
            "tools": [
                {
                    "name": "foo",
                    "function": {
                        "description": "blah blah"
                    }
                }
            ]
        }

        dict_out: Dict[str, Any] = my_filter.filter_config(dict_in)

        json_in: str = json.dumps(dict_in, indent=4, sort_keys=True)
        json_out: str = json.dumps(dict_out, indent=4, sort_keys=True)

        self.assertEqual(json_in, json_out)

    def test_parameter_replacement(self):
        """
        Tests basic operations of the ConfigFilter
        """
        my_filter = DictionaryCommonDefsConfigFilter()

        dict_in: Dict[str, Any] = {
            "commondefs": {
                "replacement_values": {
                    "cao_item": {
                        "type": "string",
                        "properties": {
                            "attribute_name": {
                                "type": "string"
                            },
                            "attribute_type": {
                                "type": "string",
                                "enum": ["categories", "FREE_RESPONSE"],
                            },
                            "choices": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            }
                        },
                        "required": ["attribute_name"]
                    }
                }
            },
            "tools": [
                {
                    "name": "prescriptor",
                    "function": {
                        "description": """
Creates a prescriptor assistant by taking the list of context, actions, and outcomes attributes, "
then, by taking the context values, returns its recommended action values.
""",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "A unique name for the current decision dialog"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "A brief description of the current decision"
                                },
                                "context_defs": {
                                    "type": "array",
                                    "description": """
An array of context attributes,
each with an attribute name and type, as int or categorical, with possible categories.
""",
                                    "items": "cao_item"
                                },
                                "actions_defs": {
                                    "type": "array",
                                    "description": """
An array of action attributes,
each with an attribute name and type, as int or categorical, with possible categories.
""",
                                    "items": "cao_item"
                                },
                                "outcomes_defs": {
                                    "type": "array",
                                    "description": """
An array of outcome attributes,
each with an attribute name and type, as int or categorical, with possible categories.
""",
                                    "items": "cao_item"
                                },
                                "context_vals": {
                                    "type": "array",
                                    "description": """
An array of context attribute values for a specific decision we need to make.""",
                                    "items": "cao_item"
                                }
                            },
                            "required": ["name", "description",
                                         "context_defs", "actions_defs", "outcomes_defs",
                                         "context_vals"],
                        }
                    },
                    "instructions": """
You are a system that, given the values of the given context attributes,
suggests values for the given action attributes in a manner
that would optimize the given outcome attributes.
The system will deliver precise and straightforward responses,
comprising only the prescribed action values.
There will be no elaboration or additional commentary.
You will consult a predictor expert by calling the predictor function in order to
generate your answers.
The predictor function takes context and action attributes and values, and predicts the outcomes.
For each outcome, a certainty value between 0 and 1 will also be returned.
""",
                    "command": "Suggest actions to optimize the outcomes given the context values.",
                    "tools": [
                        "predictor"
                    ]
                }
            ]
        }

        dict_out: Dict[str, Any] = my_filter.filter_config(dict_in)
        dicts: Dict[str, Any] = dict_out.get("commondefs").get("replacement_values")
        prescriptor: Dict[str, Any] = dict_out.get("tools")[0]

        extractor = DictionaryExtractor(prescriptor)

        # Go down the hierarchy to be sure we are getting what we want
        self.assertEqual(extractor.get("name"), "prescriptor")
        self.assertIsInstance(extractor.get("function"), Dict)
        self.assertIsInstance(extractor.get("function.parameters"), Dict)
        self.assertIsInstance(extractor.get("function.parameters.properties"), Dict)
        self.assertIsInstance(extractor.get("function.parameters.properties.context_defs"), Dict)
        self.assertIsInstance(extractor.get("function.parameters.properties.context_defs.items"), Dict)

        # See if the whole dict is there and matches
        items_str = json.dumps(extractor.get("function.parameters.properties.context_defs.items"),
                               indent=4, sort_keys=True)
        dicts_str = json.dumps(dicts.get("cao_item"), indent=4, sort_keys=True)
        self.assertEqual(items_str, dicts_str)
