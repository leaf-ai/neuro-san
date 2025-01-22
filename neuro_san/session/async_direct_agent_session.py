
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

from asyncio import Future
from copy import copy

from leaf_common.asyncio.asyncio_executor import AsyncioExecutor
from leaf_common.parsers.dictionary_extractor import DictionaryExtractor

from neuro_san.internals.chat.chat_session import ChatSession
from neuro_san.internals.chat.connectivity_reporter import ConnectivityReporter
from neuro_san.internals.chat.data_driven_chat_session import DataDrivenChatSession
from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.internals.graph.tools.front_man import FrontMan
from neuro_san.session.agent_session import AgentSession
from neuro_san.session.chat_session_map import ChatSessionMap


class AsyncDirectAgentSession:
    """
    Direct guts for an AgentSession.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self,
                 chat_session_map: ChatSessionMap,
                 tool_registry: AgentToolRegistry,
                 asyncio_executor: AsyncioExecutor,
                 metadata: Dict[str, Any] = None,
                 security_cfg: Dict[str, Any] = None):
        """
        Constructor

        :param chat_session_map: The global ChatSessionMap for the service.
        :param tool_registry: The AgentToolRegistry to use for the session.
        :param asyncio_executor: The global AsyncioExecutor for running
                        stuff in the background.
        :param metadata: A dictionary of request metadata to be forwarded
                        to subsequent yet-to-be-made requests.
        :param security_cfg: A dictionary of parameters used to
                        secure the TLS and the authentication of the gRPC
                        connection.  Supplying this implies use of a secure
                        GRPC Channel.  If None, uses insecure channel.
        """
        # These aren't used yet
        self._metadata: Dict[str, Any] = metadata
        self._security_cfg: Dict[str, Any] = security_cfg
        self.chat_session_map: ChatSessionMap = chat_session_map
        self.asyncio_executor: AsyncioExecutor = asyncio_executor
        self.we_created_executor: bool = False
        self.tool_registry: AgentToolRegistry = tool_registry

        # For convenience
        if self.asyncio_executor is None:
            self.we_created_executor = True
            self.asyncio_executor = AsyncioExecutor()
            self.asyncio_executor.start()

    async def function(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the FunctionRequest
                    protobufs structure. Has the following keys:
                        <None>
        :return: A dictionary version of the FunctionResponse
                    protobufs structure. Has the following keys:
                "function" - the dictionary description of the function
                "status" - status for finding the function.
        """
        _ = request_dict
        response_dict: Dict[str, Any] = {
            "status": AgentSession.NOT_FOUND
        }

        front_man: FrontMan = self.tool_registry.create_front_man(None, None)
        if front_man is not None:
            spec: Dict[str, Any] = front_man.get_agent_tool_spec()
            empty: Dict[str, Any] = {}
            function: Dict[str, Any] = spec.get("function", empty)
            response_dict = {
                "function": function,
                "status": AgentSession.FOUND
            }

        return response_dict

    async def connectivity(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the ConnectivityRequest
                    protobufs structure. Has the following keys:
                        <None>
        :return: A dictionary version of the ConnectivityResponse
                    protobufs structure. Has the following keys:
                "connectivity_info" - the list of connectivity descriptions for
                                    each node in the agent network the service
                                    wants the client ot know about.
                "status" - status for finding the function.
        """
        _ = request_dict
        response_dict: Dict[str, Any] = {
            "status": AgentSession.NOT_FOUND
        }

        reporter = ConnectivityReporter(self.tool_registry)
        connectivity_info: List[Dict[str, Any]] = reporter.report_network_connectivity()
        response_dict = {
            "connectivity_info": connectivity_info,
            "status": AgentSession.FOUND
        }

        return response_dict

    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    async def streaming_chat(self, request_dict: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        :param request_dict: A dictionary version of the ChatRequest
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
                              Upon first contact this can be blank.
            "user_input"    - A string representing the user input to the chat stream

        :return: An iterator of dictionary versions of the ChatResponse
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
                              This will always be filled upon response.
            "status"        - An int representing the chat session's status. Can be one of:
                              FOUND     - The given session_id is alive and well
                                          on this service instance and the user_input
                                          has been registered in the chat stream.
                              NOT_FOUND - Returned if the service instance does not find
                                          the session_id given in the request.
                                          For continuing chat streams, this could imply
                                          a series of client-side retries as multiple
                                          service instances will not keep track of the same
                                          chat sessions.
                              CREATED   - Returned when no session_id was given (initiation
                                          of new chat by client) and a new chat session is created.
            "response"      - An optional ChatMessage dictionary.  See chat.proto for details.

            Note that responses to the chat input might be numerous and will come as they
            are produced until the system decides there are no more messages to be sent.
        """
        extractor = DictionaryExtractor(request_dict)

        # Get the user input. Prefer the newer-style from the user_message
        user_input: str = request_dict.get("user_input")
        user_input = extractor.get("user_message.text", user_input)

        session_id: str = request_dict.get("session_id")
        sly_data: Dict[str, Any] = request_dict.get("sly_data")
        status: int = AgentSession.NOT_FOUND

        chat_session: ChatSession = self.chat_session_map.get_chat_session(session_id)
        if chat_session is None:
            if session_id is None:
                # Initiate a new conversation.
                status = AgentSession.CREATED
                chat_session = DataDrivenChatSession(registry=self.tool_registry)
                session_id = self.chat_session_map.register_chat_session(chat_session)
            else:
                # We got an session_id, but this service instance has no knowledge
                # of it.
                status = AgentSession.NOT_FOUND
        else:
            # We have seen this session_id before and can register new user input.
            status = AgentSession.FOUND

        # Prepare the response dictionary
        template_response_dict = {
            "session_id": session_id,
            "status": status
        }

        if chat_session is None or user_input is None:
            # Can't go on to chat, so report back early with a single value.
            # There is no ChatMessage response in the dictionary in this case
            yield template_response_dict
            return

        # Create an asynchronous background task to process the user input.
        # This might take a few minutes, which can be longer than some
        # sockets stay open.
        future: Future = self.asyncio_executor.submit(session_id, chat_session.streaming_chat,
                                                      user_input, sly_data)
        # Ignore the future. Live in the now.
        _ = future

        # The generator below will asynchronously block waiting for
        # chat.ChatMessage dictionaries to come back asynchronously from the submit()
        # above until there are no more from the input.
        generator = chat_session.get_queue()
        for message in generator:

            response_dict: Dict[str, Any] = copy(template_response_dict)
            if any(message):
                # We expect the message to be a dictionary form of chat.ChatMessage
                response_dict["response"] = message
                yield response_dict

    def close(self):
        """
        Tears down resources created
        """
        if self.we_created_executor and self.asyncio_executor is not None:
            self.asyncio_executor.shutdown()
            self.asyncio_executor = None
