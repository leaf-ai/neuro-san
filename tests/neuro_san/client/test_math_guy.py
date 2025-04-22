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

from unittest import TestCase

from tests.framework.driver.data_driven_agent_test_driver import DataDrivenAgentTestDriver
from tests.framework.pytest.unit_test_assert_forwarder import UnitTestAssertForwarder


class TestMathGuy(TestCase):
    """
    Tests basic functionality via the math_guy agent.
    """

    def test_basic_sly_data(self):
        """
        Tests basic sly_data going to and from an agent network.
        """
        asserts = UnitTestAssertForwarder(self)
        agent_test = DataDrivenAgentTestDriver(asserts)
        agent_test.one_test("math_guy/basic_sly_data.hocon")

    def test_forwarded_sly_data(self):
        """
        Tests forwarded sly_data going to and from an agent network.
        """
        asserts = UnitTestAssertForwarder(self)
        agent_test = DataDrivenAgentTestDriver(asserts)
        agent_test.one_test("math_guy/forwarded_sly_data.hocon")
