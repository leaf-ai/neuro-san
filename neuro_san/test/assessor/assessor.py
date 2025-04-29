
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
from typing import List

import argparse

from neuro_san.client.agent_session_factory import AgentSessionFactory
from neuro_san.client.streaming_input_processor import StreamingInputProcessor
from neuro_san.interfaces.agent_session import AgentSession
from neuro_san.internals.utils.file_of_class import FileOfClass
from neuro_san.message_processing.basic_message_processor import BasicMessageProcessor
from neuro_san.test.assessor.assessor_assert_forwarder import AssessorAssertForwarder
from neuro_san.test.driver.data_driven_agent_test_driver import DataDrivenAgentTestDriver


class Assessor:
    """
    Command line tool for assessing an agent network's response
    to an input test case.
    """

    SHIPPED_HOCONS = FileOfClass(__file__, path_to_basis="../../registries")

    def __init__(self):
        """
        Constructor
        """
        self.args = None

    def main(self):
        """
        Main entry point for command line user interaction.
        """
        # Parse command line arguments
        self.parse_args()

        # Run the tests per the test case, collecting failure information in the AssertForwarder
        asserts = AssessorAssertForwarder()
        driver = DataDrivenAgentTestDriver(asserts)
        driver.one_test(self.args.test_hocon)

        # Get raw failure information from AssertForwarder
        num_total: int = asserts.get_num_total()
        fail: List[Dict[str, Any]] = asserts.get_fail_dicts()
        num_pass: int = num_total - len(fail)

        # Initial output
        print(f"{self.args.test_hocon}:")
        print(f"{num_pass}/{num_total} attempts passed.")
        if num_pass == num_total:
            return

        failure_modes: List[str] = []
        mode_count: List[int] = []
        for one_failure in fail:
            failure_mode: str = self.categorize_one_failure(one_failure, failure_modes)
            if failure_mode in failure_modes:
                index: int = failure_modes.index(failure_mode)
                mode_count[index] = mode_count[index] + 1
            else:
                failure_modes.append(failure_mode)
                mode_count[index] = 1

        # End ouput
        print(f"{len(fail)}/{num_total} attempts failed.")
        print("Modes of failure:")
        for failure_mode, index in enumerate(failure_modes):
            print("\n")
            print(f"{mode_count[index]}/{len(fail)}:")
            print(f"{failure_mode}")

    def parse_args(self):
        """
        Parse command line arguments into member variables
        """
        arg_parser = argparse.ArgumentParser()
        self.add_args(arg_parser)
        self.args = arg_parser.parse_args()
        if self.args.assessor_agent is None:
            self.args.assessor_agent = self.SHIPPED_HOCONS.get_file_in_basis("assess_failure.hocon")

    def add_args(self, arg_parser: argparse.ArgumentParser):
        """
        Adds arguments.  Allows subclasses a chance to add their own.
        :param arg_parser: The argparse.ArgumentParser to add.
        """
        arg_parser.add_argument("--test_hocon", type=str,
                                help="The test case .hocon file to use as a basis for assessment")
        arg_parser.add_argument("--assessor_agent", type=str, default=None,
                                help="The assessor agent to use. A default of None implies use of assess_failure.hocon")
        arg_parser.add_argument("--connection", default="direct", type=str,
                                choices=["grpc", "direct", "http", "https"],
                                help="""
The type of connection to initiate. Choices are to connect to:
    "grpc"      - an agent service via gRPC. Needs host and port.
    "http"      - an agent service via HTTP. Needs host and port.
    "https"     - an agent service via secure HTTP. Needs host and port.
    "direct"    - a session via library.
""")
        arg_parser.add_argument("--host", type=str, default=None,
                                help="hostname setting if not running locally")
        arg_parser.add_argument("--port", type=int, default=AgentSession.DEFAULT_PORT,
                                help="TCP/IP port to run the Agent gRPC service on")

    def categorize_one_failure(self, fail: Dict[str, Any], failure_modes: List[str]) -> str:
        """
        Categorize a single failure instance
        :param fail: A failure dictionary from asserts.get_fail_dicts()
        :param failure_modes: A List of strings describing known failure modes
        :return: A string describing an existing mode of failure or
                a description of a new mode of failure
        """
        session: AgentSession = AgentSessionFactory().create_session(self.args.connection,
                                                                     self.args.assessor_agent,
                                                                     hostname=self.args.host,
                                                                     port=self.args.port)

        text: str = f"""
The acceptance_criteria is:
"{fail.get('acceptance_criteria')}".

The text_sample is:
"{fail.get('text_sample')}".

The known failure_modes are:
{failure_modes}
"""
        input_processor = StreamingInputProcessor(session=session)
        processor: BasicMessageProcessor = input_processor.get_message_processor()
        request: Dict[str, Any] = input_processor.formulate_chat_request(text)

        # Call streaming_chat()
        empty: Dict[str, Any] = {}
        for chat_response in session.streaming_chat(request):
            message: Dict[str, Any] = chat_response.get("response", empty)
            processor.process_message(message, chat_response.get("type"))

        raw_answer: str = processor.get_answer()
        return raw_answer


if __name__ == '__main__':
    Assessor().main()
