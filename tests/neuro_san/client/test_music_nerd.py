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

from tests.neuro_san.client.data_driven_agent_test import DataDrivenAgentTest


class TestMusicNerd(DataDrivenAgentTest):
    """
    Tests basic functionality via the music_nerd agent.
    """

    def test_conversation_history(self):
        """
        Tests a basic conversation to see if chat context is being carried over correctly.
        """
        self.one_test("music_nerd/beatles_with_history.hocon")
