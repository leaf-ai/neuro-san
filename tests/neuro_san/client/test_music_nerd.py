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

from tests.neuro_san.client.data_driven_agent_test import DataDrivenAgentTest
from tests.neuro_san.client.unit_test_assert_forwarder import UnitTestAssertForwarder


class TestMusicNerd(TestCase):
    """
    Tests basic functionality via the music_nerd agent.
    """

    def test_conversation_history(self):
        """
        Tests a basic conversation to see if chat context is being carried over correctly.
        """
        asserts = UnitTestAssertForwarder(self)
        agent_test = DataDrivenAgentTest(asserts)
        agent_test.one_test("music_nerd/beatles_with_history.hocon")
