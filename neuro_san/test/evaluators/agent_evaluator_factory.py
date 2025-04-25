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

from neuro_san.test.evaluators.gist_agent_evaluator import GistAgentEvaluator
from neuro_san.test.evaluators.keywords_agent_evaluator import KeywordsAgentEvaluator
from neuro_san.test.evaluators.value_agent_evaluator import ValueAgentEvaluator
from neuro_san.test.interfaces.agent_evaluator import AgentEvaluator
from neuro_san.test.interfaces.assert_forwarder import AssertForwarder


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
            evaluator = KeywordsAgentEvaluator(asserts, negate=False)
        elif evaluation_type == "not_keywords":
            evaluator = KeywordsAgentEvaluator(asserts, negate=True)
        elif evaluation_type == "value":
            evaluator = ValueAgentEvaluator(asserts, negate=False)
        elif evaluation_type == "not_value":
            evaluator = ValueAgentEvaluator(asserts, negate=True)
        elif evaluation_type == "gist":
            evaluator = GistAgentEvaluator(asserts, negate=False)
        elif evaluation_type == "not_gist":
            evaluator = GistAgentEvaluator(asserts, negate=True)

        return evaluator
