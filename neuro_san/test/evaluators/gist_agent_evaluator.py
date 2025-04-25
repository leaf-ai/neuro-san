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

from neuro_san.client.agent_session_factory import AgentSessionFactory
from neuro_san.client.streaming_input_processor import StreamingInputProcessor
from neuro_san.interfaces.agent_session import AgentSession
from neuro_san.message_processing.basic_message_processor import BasicMessageProcessor
from neuro_san.test.evaluators.abstract_agent_evaluator import AbstractAgentEvaluator


class GistAgentEvaluator(AbstractAgentEvaluator):
    """
    AbstractAgentEvaluator implementation that looks asks an LLM if the test values
    match the gist of the value to be verified against.
    """

    def test_one(self, verify_value: Any, test_value: Any):
        """
        :param verify_value: The value to verify against
        :param test_value: The value appearing in the test sample
        """

        pass_fail: bool = self.ask_llm(acceptance_criteria=str(verify_value),
                                       text_sample=str(test_value))

        # Make the exception messaging agree with the sense of the negation.
        # That is: When we are playing it straight (no negation), the assertion
        # fails because the text sample didn't match the acceptance criteria
        # and that failure is unexpected.  When the negation is in place,
        # it is unexpected that it actually *did* match the acceptance criteria.
        did_str: str = "didn't"
        if self.negate:
            did_str = "did"

        message: str = f"""
text_sample unexpectedly {did_str} match acceptance criteria.

text_sample:
{test_value}

acceptance_criteria:
{verify_value}
"""
        if self.negate:
            self.asserts.assertFalse(pass_fail, msg=message)
        else:
            self.asserts.assertTrue(pass_fail, msg=message)

    def ask_llm(self, acceptance_criteria: str, text_sample: str) -> bool:
        """
        Asks an llm if a text_sample meets a description of acceptance_criteria

        :param acceptance_criteria: String description of the acceptance criteria
                    of the text sample
        :param text_sample: A sample of text to evaluate
        :return: A boolean value as to whether or not the text_sample passes the acceptance_criteria.
        """
        text: str = f"""
The acceptance_criterion is:
"{acceptance_criteria}".

The text_sample is:
"{text_sample}".
"""

        # Use the "gist" agent to do the evalution
        session: AgentSession = AgentSessionFactory().create_session("direct", "gist")
        input_processor = StreamingInputProcessor(session=session)
        processor: BasicMessageProcessor = input_processor.get_message_processor()
        request: Dict[str, Any] = input_processor.formulate_chat_request(text)

        # Call streaming_chat()
        empty: Dict[str, Any] = {}
        for chat_response in session.streaming_chat(request):
            message: Dict[str, Any] = chat_response.get("response", empty)
            processor.process_message(message, chat_response.get("type"))

        raw_answer: str = processor.get_answer()
        answer: str = raw_answer.lower()
        test_passes: bool = self.determine_pass_fail(answer)
        return test_passes

    def determine_pass_fail(self, answer: str) -> bool:
        """
        :param answer: The answer from the conversation with the LLM
        :return: True if the test had passed.
        """
        # Determine pass/fail by examining the answer
        passing: bool = "pass" in answer
        failing: bool = "fail" in answer

        # Be sure there is no equivocating.
        test_passes: bool = passing and not failing
        test_fails: bool = failing and not passing
        only_one: bool = test_passes or test_fails
        self.asserts.assertTrue(only_one)

        return test_passes
