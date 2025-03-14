
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

from neuro_san.interfaces.async_agent_session import AsyncAgentSession
from neuro_san.internals.chat.connectivity_reporter import ConnectivityReporter
from neuro_san.internals.chat.data_driven_chat_session import DataDrivenChatSession
from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.internals.graph.tools.front_man import FrontMan
from neuro_san.session.session_invocation_context import SessionInvocationContext


class AsyncDirectAgentSession(AsyncAgentSession):
    """
    Direct guts for an AsyncAgentSession.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self,
                 tool_registry: AgentToolRegistry,
                 invocation_context: SessionInvocationContext,
                 metadata: Dict[str, Any] = None,
                 security_cfg: Dict[str, Any] = None):
        """
        Constructor

        :param tool_registry: The AgentToolRegistry to use for the session.
        :param invocation_context: The SessionInvocationContext to use to consult
                        for policy objects scoped at the invocation level.
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

        self.invocation_context: SessionInvocationContext = invocation_context
        self.tool_registry: AgentToolRegistry = tool_registry
        self.request_id: str = None
        if metadata is not None:
            self.request_id = metadata.get("request_id")

    async def function(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the FunctionRequest
                    protobufs structure. Has the following keys:
                        <None>
        :return: A dictionary version of the FunctionResponse
                    protobufs structure. Has the following keys:
                "function" - the dictionary description of the function
        """
        _ = request_dict
        response_dict: Dict[str, Any] = {
        }

        front_man: FrontMan = self.tool_registry.create_front_man()
        if front_man is not None:
            spec: Dict[str, Any] = front_man.get_agent_tool_spec()
            empty: Dict[str, Any] = {}
            function: Dict[str, Any] = spec.get("function", empty)
            response_dict = {
                "function": function,
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
        """
        _ = request_dict
        response_dict: Dict[str, Any] = {
        }

        reporter = ConnectivityReporter(self.tool_registry)
        connectivity_info: List[Dict[str, Any]] = reporter.report_network_connectivity()
        response_dict = {
            "connectivity_info": connectivity_info,
        }

        return response_dict

    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    async def streaming_chat(self, request_dict: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        :param request_dict: A dictionary version of the ChatRequest
                    protobufs structure. Has the following keys:
            "user_message" - A ChatMessage dict representing the user input to the chat stream
            "chat_context" - A ChatContext dict representing the state of the previous conversation
                            (if any)
        :return: An iterator of dictionary versions of the ChatResponse
                    protobufs structure. Has the following keys:
            "response"      - An optional ChatMessage dictionary.  See chat.proto for details.

            Note that responses to the chat input might be numerous and will come as they
            are produced until the system decides there are no more messages to be sent.
        """
        extractor = DictionaryExtractor(request_dict)

        # Get the user input. Prefer the newer-style from the user_message
        user_input: str = request_dict.get("user_input")
        user_input = extractor.get("user_message.text", user_input)

        chat_context: Dict[str, Any] = request_dict.get("chat_context")
        sly_data: Dict[str, Any] = request_dict.get("sly_data")

        chat_session = DataDrivenChatSession(registry=self.tool_registry)

        # Prepare the response dictionary
        template_response_dict = {
        }

        if chat_session is None or user_input is None:
            # Can't go on to chat, so report back early with a single value.
            # There is no ChatMessage response in the dictionary in this case
            yield template_response_dict
            return

        # Create an asynchronous background task to process the user input.
        # This might take a few minutes, which can be longer than some
        # sockets stay open.
        asyncio_executor: AsyncioExecutor = self.invocation_context.get_asyncio_executor()
        future: Future = asyncio_executor.submit(self.request_id, chat_session.streaming_chat,
                                                 user_input, self.invocation_context, sly_data,
                                                 chat_context)
        # Ignore the future. Live in the now.
        _ = future

        # The generator below will asynchronously block waiting for
        # chat.ChatMessage dictionaries to come back asynchronously from the submit()
        # above until there are no more from the input.
        generator = self.invocation_context.get_queue()
        async for message in generator:

            response_dict: Dict[str, Any] = copy(template_response_dict)
            if any(message):
                # We expect the message to be a dictionary form of chat.ChatMessage
                response_dict["response"] = message
                yield response_dict

    def close(self):
        """
        Tears down resources created
        """
        if self.invocation_context is None:
            return
        self.invocation_context.close()
        self.invocation_context = None
