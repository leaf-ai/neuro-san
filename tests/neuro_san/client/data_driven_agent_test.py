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
from typing import Generator
from typing import List
from typing import Union

from datetime import datetime

from leaf_common.persistence.easy.easy_hocon_persistence import EasyHoconPersistence

from neuro_san.client.agent_session_factory import AgentSessionFactory
from neuro_san.client.streaming_input_processor import StreamingInputProcessor
from neuro_san.interfaces.agent_session import AgentSession
from neuro_san.internals.utils.file_of_class import FileOfClass
from neuro_san.message_processing.basic_message_processor import BasicMessageProcessor
from neuro_san.session.direct_agent_session import DirectAgentSession

from tests.neuro_san.client.agent_evaluator import AgentEvaluator
from tests.neuro_san.client.agent_evaluator_factory import AgentEvaluatorFactory
from tests.neuro_san.client.assert_forwarder import AssertForwarder


class DataDrivenAgentTest:
    """
    Abstract test class whose subclasses define hocon file to parse as test cases.
    """

    TEST_KEYS: List[str] = ["text", "sly_data"]

    def __init__(self, asserts: AssertForwarder, fixtures: FileOfClass = None):
        """
        Constructor
        :param asserts: The AssertForwarder instance to use to integrate failures
                        back into the test system.
        :param fixtures: Optional path to the fixtures root.
        """
        self.asserts: AssertForwarder = asserts
        self.fixtures: FileOfClass = fixtures
        if self.fixtures is None:
            self.fixtures = FileOfClass(__file__, path_to_basis="../../fixtures")

    def one_test(self, hocon_file: str):
        """
        Use a single hocon file in the fixtures as a test case"

        :param hocon_file: The name of the hocon from the fixtures directory.
        """
        test_case: Dict[str, Any] = self.parse_hocon_test_case(hocon_file)

        # Get the agent to use
        agent: str = test_case.get("agent")
        self.asserts.assertIsNotNone(agent)

        # Get the connection type
        connections: Union[List[str], str] = test_case.get("connections")
        if connections is None:
            # Assume direct if not specified
            connections = ["direct"]
        elif isinstance(connections, str):
            # Make single strings into a list for consistent parsing
            connections = [connections]
        self.asserts.assertIsInstance(connections, List)
        self.asserts.assertTrue(len(connections) > 0)

        # Collect the interations to test for
        empty: List[Any] = []
        interactions: List[Dict[str, Any]] = test_case.get("interactions", empty)
        self.asserts.assertTrue(len(interactions) > 0)

        # Collect other session information
        use_direct: bool = test_case.get("use_direct", False)
        metadata: Dict[str, Any] = test_case.get("metadata", None)

        for connection in connections:

            session: AgentSession = AgentSessionFactory().create_session(connection,
                                                                         agent,
                                                                         use_direct=use_direct,
                                                                         metadata=metadata)
            chat_context: Dict[str, Any] = None
            for interaction in interactions:
                if isinstance(session, DirectAgentSession):
                    session.reset()
                chat_context = self.interact(agent, session, interaction, chat_context)

    def parse_hocon_test_case(self, hocon_file: str) -> Dict[str, Any]:
        """
        Use a single hocon file in the fixtures as a test case"

        :param hocon_file: The name of the hocon from the fixtures directory.
        """
        test_path: str = self.fixtures.get_file_in_basis(hocon_file)
        hocon = EasyHoconPersistence()
        test_case: Dict[str, Any] = hocon.restore(file_reference=test_path)
        return test_case

    # pylint: disable=too-many-locals
    def interact(self, agent: str, session: AgentSession, interaction: Dict[str, Any],
                 chat_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interact with an agent and evaluate its output

        :param session: The AgentSession to work with
        :param interaction: The interaction dictionary to base evalaution off of.
        """
        _ = agent       # For now
        empty: Dict[str, Any] = {}

        # Prepare the processor
        now = datetime.now()
        datestr: str = now.strftime("%Y-%m-%d-%H:%M:%S")
        thinking_dir: str = f"/tmp/agent_test/{datestr}_agent"
        input_processor = StreamingInputProcessor("", None, session, thinking_dir)
        processor: BasicMessageProcessor = input_processor.processor

        # Prepare the request
        text: str = interaction.get("text")
        sly_data: str = interaction.get("sly_data")
        chat_filter: Dict[str, Any] = {
            "chat_filter_type": interaction.get("chat_filter", "MINIMAL")
        }
        request: Dict[str, Any] = input_processor.formulate_chat_request(text, sly_data, chat_context, chat_filter)

        # Call streaming_chat()
        chat_responses: Generator[Dict[str, Any], None, None] = session.streaming_chat(request)
        for chat_response in chat_responses:
            message = chat_response.get("response", empty)
            processor.process_message(message, chat_response.get("type"))

        # Evaluate response
        response: Dict[str, Any] = interaction.get("response", empty)

        # Look for a block for each ChatMessage section key to test
        for test_key in self.TEST_KEYS:
            response_section: Dict[str, Any] = response.get(test_key, empty)
            for one_evaluation, verify_for in response_section.items():
                # Evaluate each item in the test block
                evaluator: AgentEvaluator = AgentEvaluatorFactory.create_evaluator(self.asserts,
                                                                                   one_evaluation,
                                                                                   test_key)
                evaluator.evaluate(processor, verify_for)

        # See how we should continue the conversation
        return_chat_context: Dict[str, Any] = None
        if interaction.get("continue_conversation", True):
            return_chat_context = processor.get_chat_context()

        return return_chat_context
