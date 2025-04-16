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
from typing import List

from neuro_san.message_processing.basic_message_processor import BasicMessageProcessor

from tests.neuro_san.client.agent_evaluator import AgentEvaluator


class KeywordsAgentEvaluator(AgentEvaluator):
    """
    AgentEvaluator implementation that looks for specific keywords in output.
    """

    def __init__(self, test_key: str):
        """
        Constructor
        :param test_key: The chat message key to look for output
        """
        self.test_key: str = test_key

    def evaluate(self, processor: BasicMessageProcessor, verify_for: Any):
        """
        Evaluate the contents of the BasicMessageProcessor

        :param processor: The BasicMessageProcessor to evaluate
        :param verify_for: The data to evaluate the response against
        """
        test_me: str = None

        if self.test_key == "text":
            test_me = processor.get_answer()
        elif self.test_key == "sly_data":
            # Not yet
            return

        self.assertIsNotNone(test_me)

        verify_all: List[str] = verify_for
        if isinstance(verify_for, str):
            verify_all = [verify_for]
        self.assertIsInstance(verify_all, List)

        for verify_one in verify_all:
            self.assertIn(verify_one, test_me)
