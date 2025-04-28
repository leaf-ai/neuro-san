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

from neuro_san.test.interfaces.assert_forwarder import AssertForwarder


class AssessorAssertForwarder(AssertForwarder):
    """
    AssertForwarder implemetation for the agent Assessor.
    """

    def __init__(self):
        """
        Constructor
        """
        self.num_total: int = 0
        self.fail: List[Dict[str, Any]] = []

    def get_num_total(self) -> int:
        """
        :return: The total number of test cases seen
        """
        return self.num_total

    def get_fail_dicts(self) -> List[Dict[str, Any]]:
        """
        :return: The failure dictionaries for further analysis
        """
        return self.fail

    def assertTrue(self, expr: Any, msg: str = None):
        """
        Assert that the expression is true

        :param expr: Expression to test
        :param msg: optional string message
        """
        self.handle_assert(bool(expr), True, msg)

    def assertFalse(self, expr: Any, msg: str = None):
        """
        Assert that the expression is false

        :param expr: Expression to test
        :param msg: optional string message
        """
        self.handle_assert(bool(expr), False, msg)

    def handle_assert(self, is_passing: bool, sense: bool, msg: str):
        """
        Handle the assert.
        :param is_passing: Boolean as to whether or not the test is passing.
        :param sense: Whether the test was supposed to be true or false.
        :param msg: The assert message to parse.
        """
        self.num_total += 1
        if is_passing == sense:
            return

        components: Dict[str, Any] = self.parse_assert_message(msg)
        components["sense"] = sense
        self.fail.append(components)

    def parse_assert_message(self, message: str) -> Dict[str, Any]:
        """
        Parse a single assert message into its parts.
        :param message: The assert message from GistAgentEvaluator
        :return: A dictionary with the relevant components of the message
        """

        # See GistAgentEvaluator for format.
        acceptance_split: List[str] = message.split("acceptance_criteria:")
        sample_split: List[str] = acceptance_split[0].split("text_sample:")

        components: Dict[str, Any] = {
            # Get what comes after the "acceptance_criteria" delimiter
            "acceptance_criteria": acceptance_split[-1],

            # Get what comes after the "text_sample" delimiter
            "text_sample": sample_split[-1]
        }
        return components

    def assertEqual(self, first: Any, second: Any, msg: str = None):
        """
        Assert that the first is equal to the second

        :param first: First comparison element
        :param second: Second comparison element
        :param msg: optional string message
        """
        pass

    def assertNotEqual(self, first: Any, second: Any, msg: str = None):
        """
        Assert that the first is not equal to the second

        :param first: First comparison element
        :param second: Second comparison element
        :param msg: optional string message
        """
        pass

    def assertIs(self, first: Any, second: Any, msg: str = None):
        """
        Assert that the first and second are the same object

        :param first: First comparison element
        :param second: Second comparison element
        :param msg: optional string message
        """
        pass

    def assertIsNot(self, first: Any, second: Any, msg: str = None):
        """
        Assert that the first and second are not the same object

        :param first: First comparison element
        :param second: Second comparison element
        :param msg: optional string message
        """
        pass

    def assertIsNone(self, expr: Any, msg: str = None):
        """
        Assert that the expression is None

        :param expr: Expression to test
        :param msg: optional string message
        """
        pass

    def assertIsNotNone(self, expr: Any, msg: str = None):
        """
        Assert that the expression is not None

        :param expr: Expression to test
        :param msg: optional string message
        """
        pass

    def assertIn(self, member: Any, container: Any, msg: str = None):
        """
        Assert that the member is in the container

        :param member: Member comparison element
        :param container: Container comparison element
        :param msg: optional string message
        """
        pass

    def assertNotIn(self, member: Any, container: Any, msg: str = None):
        """
        Assert that the member is not in the container

        :param member: Member comparison element
        :param container: Container comparison element
        :param msg: optional string message
        """
        pass

    # pylint: disable=invalid-name
    def assertIsInstance(self, obj: Any, cls: Any, msg: str = None):
        """
        Assert that the obj is an instance of the cls

        :param obj: object instance comparison element
        :param cls: Class comparison element
        :param msg: optional string message
        """
        pass

    # pylint: disable=invalid-name
    def assertNotIsInstance(self, obj: Any, cls: Any, msg: str = None):
        """
        Assert that the obj is not an instance of the cls

        :param obj: object instance comparison element
        :param cls: Class comparison element
        :param msg: optional string message
        """
        pass
