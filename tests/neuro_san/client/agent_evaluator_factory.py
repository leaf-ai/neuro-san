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

from tests.neuro_san.client.agent_evaluator import AgentEvaluator
from tests.neuro_san.client.assert_forwarder import AssertForwarder
from tests.neuro_san.client.keywords_agent_evaluator import KeywordsAgentEvaluator
from tests.neuro_san.client.value_agent_evaluator import ValueAgentEvaluator


class AgentEvaluatorFactory:
    """
    Factory that creates AgentEvaluators
    """

    @staticmethod
    def create_evaluator(asserts: AssertForwarder, evaluation_type: str) -> AgentEvaluator:
        """
        Creates AgentEvaluators

        :param asserts: The AssertForwarder instance to handle failures
        :param evaluation_type: A string key describing how the evaluation will take place
        """
        evaluator: AgentEvaluator = None

        if evaluation_type == "keywords":
            evaluator = KeywordsAgentEvaluator(asserts)
        elif evaluation_type == "value":
            evaluator = ValueAgentEvaluator(asserts)

        return evaluator
