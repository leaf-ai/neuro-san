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

from tests.neuro_san.client.agent_evaluator import AgentEvaluator
from tests.neuro_san.client.keywords_agent_evaluator import KeywordsAgentEvaluator


class AgentEvaluatorFactory:
    """
    Factory that creates AgentEvaluators
    """

    @staticmethod
    def create_evaluator(test_case: TestCase, evaluation_type: str, test_key: str) -> AgentEvaluator:
        """
        Creates AgentEvaluators

        :param evaluation_type: A string key describing how the evaluation will take place
        :param test_key: The test key describing the portion of the ChatMessage contents to evaluate
        """
        evaluator: AgentEvaluator = None

        if evaluation_type == "keywords":
            evaluator = KeywordsAgentEvaluator(test_case, test_key)

        return evaluator
