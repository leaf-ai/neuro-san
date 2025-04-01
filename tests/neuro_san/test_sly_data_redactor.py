
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

from unittest import TestCase

from neuro_san.internals.graph.tools.sly_data_redactor import SlyDataRedactor


class TestSlyDataRedactor(TestCase):
    """
    Unit tests for SlyDataRedactor class.
    """

    def test_assumptions(self):
        """
        Can we construct?
        """
        agent_spec = None
        redactor = SlyDataRedactor(agent_spec)
        self.assertIsNotNone(redactor)

    def test_true_false(self):
        """
        Tests basic true/false operations of the SlyDataRedactor
        """
        agent_spec = {
            "allow": {
                "sly_data": {
                    "yes": True,
                    "no": False
                }
            }
        }
        redactor = SlyDataRedactor(agent_spec, config_keys=["allow.sly_data"])

        sly_data = {
            "yes": 1,
            "no": 0,
            "not_mentioned": -1,
        }

        redacted: Dict[str, Any] = redactor.filter_config(sly_data)

        self.assertIsNotNone(redacted.get("yes"))
        self.assertIsNone(redacted.get("no"))
        self.assertIsNone(redacted.get("not_mentioned"))

    def test_brute_force_true(self):
        """
        Tests the let-everything-through case of the SlyDataRedactor
        """
        agent_spec = {
            "allow": {
                "sly_data": True
            }
        }
        redactor = SlyDataRedactor(agent_spec, config_keys=["allow.sly_data"])

        sly_data = {
            "yes": 1,
            "no": 0,
            "not_mentioned": -1,
        }

        redacted: Dict[str, Any] = redactor.filter_config(sly_data)

        self.assertIsNotNone(redacted.get("yes"))
        self.assertIsNotNone(redacted.get("no"))
        self.assertIsNotNone(redacted.get("not_mentioned"))

    def test_brute_force_false(self):
        """
        Tests explicit let-nothing-through case of the SlyDataRedactor
        """
        agent_spec = {
            "allow": {
                "sly_data": False
            }
        }
        redactor = SlyDataRedactor(agent_spec, config_keys=["allow.sly_data"])

        sly_data = {
            "yes": 1,
            "no": 0,
            "not_mentioned": -1,
        }

        redacted: Dict[str, Any] = redactor.filter_config(sly_data)

        self.assertIsNone(redacted.get("yes"))
        self.assertIsNone(redacted.get("no"))
        self.assertIsNone(redacted.get("not_mentioned"))

    def test_no_spec(self):
        """
        Tests implicit let-nothing-through case of the SlyDataRedactor
        """
        agent_spec = {
        }
        redactor = SlyDataRedactor(agent_spec, config_keys=["allow.sly_data"])

        sly_data = {
            "yes": 1,
            "no": 0,
            "not_mentioned": -1,
        }

        redacted: Dict[str, Any] = redactor.filter_config(sly_data)

        self.assertIsNone(redacted.get("yes"))
        self.assertIsNone(redacted.get("no"))
        self.assertIsNone(redacted.get("not_mentioned"))

    def test_translation(self):
        """
        Tests translation of keys for the SlyDataRedactor
        """
        agent_spec = {
            "allow": {
                "sly_data": {
                    "yes": "affirmative",
                    "no": "negative"
                }
            }
        }
        redactor = SlyDataRedactor(agent_spec, config_keys=["allow.sly_data"])

        sly_data = {
            "yes": 1,
            "no": 0,
            "not_mentioned": -1,
        }

        redacted: Dict[str, Any] = redactor.filter_config(sly_data)

        self.assertIsNone(redacted.get("yes"))
        self.assertIsNone(redacted.get("no"))
        self.assertIsNone(redacted.get("not_mentioned"))
        self.assertIsNotNone(redacted.get("affirmative"))
        self.assertIsNotNone(redacted.get("negative"))
