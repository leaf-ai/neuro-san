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

from leaf_common.parsers.dictionary_extractor import DictionaryExtractor
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
        processor: BasicMessageProcessor = input_processor.get_message_processor()

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
        response_extractor = DictionaryExtractor(response)
        self.test_response_keys(processor, response_extractor, self.TEST_KEYS)

        # See how we should continue the conversation
        return_chat_context: Dict[str, Any] = None
        if interaction.get("continue_conversation", True):
            return_chat_context = processor.get_chat_context()

        return return_chat_context

    def test_response_keys(self, processor: BasicMessageProcessor,
                           response_extractor: DictionaryExtractor,
                           keys: List[str]):
        """
        Tests the given response keys

        :param processor: The BasicMessageProcessor instance to query results from.
        :param response_extractor: The DictionaryExtractor for the test structure from the test hocon file.
        :param keys: The response keys to test
        """
        deeper_test_keys: List[str] = []

        for test_key in keys:

            test_key_value: Dict[str, Any] = response_extractor.get(test_key)
            if test_key_value is None:
                # Got nothing for test_key. Nothing to see here. Please move along.
                continue

            if isinstance(test_key_value, Dict):
                # The value refers to a deeper dictionary test
                for deeper_key in test_key_value.keys():
                    deeper_test_keys.append(f"{test_key}.{deeper_key}")
            else:
                # The last part of the test_key refers to a specific evaluator type.
                split: List[str] = test_key.split(".")
                evaluator_type: str = split[-1]            # Last component of .-delimited key
                verify_key: str = ".".join(split[:-1])      # All but last component of .-delimited key
                evaluator: AgentEvaluator = AgentEvaluatorFactory.create_evaluator(self.asserts,
                                                                                   evaluator_type)
                if evaluator is not None:
                    evaluator.evaluate(processor, verify_key, test_key_value)

        # Recurse if there are further dictionary specs to dive into
        if len(deeper_test_keys) > 0:
            self.test_response_keys(processor, response_extractor, deeper_test_keys)
