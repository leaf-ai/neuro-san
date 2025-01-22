
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
from typing import AsyncGenerator
from typing import Dict
from typing import List

import json

from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.chat_message_type import ChatMessageType
from neuro_san.internals.run_context.interfaces.callable_tool import CallableTool
from neuro_san.internals.run_context.interfaces.run_context import RunContext
from neuro_san.internals.run_context.utils.external_agent_session_factory \
    import ExternalAgentSessionFactory
from neuro_san.session.agent_session import AgentSession


class ExternalTool(CallableTool):
    """
    CallableTool implementation that handles using a service to call
    another agent hierarchy as a tool.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, parent_run_context: RunContext,
                 journal: Journal,
                 agent_url: str,
                 arguments: Dict[str, Any],
                 sly_data: Dict[str, Any]):
        """
        Constructor

        :param parent_run_context: The parent RunContext (if any) to pass
                             down its resources to a new RunContext created by
                             this call.
        :param journal: The Journal that captures messages for user output
        :param agent_url: The string url to find the external agent.
                        Theoretically this has already been verified by use of an
                        ExternalAgentParsing method.
        :param arguments: A dictionary of the tool function arguments passed in
        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be an empty dictionary.
                 This gets passed along as a distinct argument to the referenced python class's
                 invoke() method.
        """
        _ = parent_run_context, journal
        self.agent_url: str = agent_url
        self.arguments: Dict[str, Any] = arguments
        self.sly_data: Dict[str, Any] = sly_data

        self.session: AgentSession = None
        self.session_id: str = None

    async def build(self) -> List[Any]:
        """
        Main entry point to the class.
        :return: A List of messages produced during this process.
        """
        message_list: List[Dict[str, Any]] = []

        # Create an AgentSession if necessary
        if self.session is None:
            factory = ExternalAgentSessionFactory()
            self.session = factory.create_session(self.agent_url)

        # Send off the input
        chat_request: Dict[str, Any] = self.gather_input(f"```json\n{json.dumps(self.arguments)}```",
                                                         self.sly_data)

        # Note that we are not await-ing the response here because what is returned is a generator.
        # Proper await-ing for generator results is done in the "async for"-loop below.
        chat_responses: AsyncGenerator[Dict[str, Any], None] = self.session.streaming_chat(chat_request)

        # The asynchronous generator will wait until the next response is available
        # from the stream.  When the other side is done, the iterator will exit the loop.
        async for chat_response in chat_responses:

            response: Dict[str, Any] = chat_response.get("response")
            if response is None:
                # Ignore messages with no response.
                continue

            session_id: str = chat_response.get("session_id")
            if session_id is not None:
                self.session_id = session_id

            response_type = response.get("type")
            message_type: ChatMessageType = ChatMessageType.from_response_type(response_type)
            text: str = response.get("text")

            # In terms of sending tool results back up the graph,
            # we really only care about immediately are the AI responses.
            # Eventually we will care about a fuller chat history.
            if message_type == ChatMessageType.AI and text is not None:

                # Prepare the output
                message: Dict[str, Any] = {
                    "role": "assistant",
                    "content": text
                }
                message_list.append(message)

        messages_str: str = json.dumps(message_list)
        return messages_str

    def gather_input(self, agent_input: str, sly_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send input to the external agent
        :param agent_input: A single string to send as input to the agent
        :param sly_data: Any private sly_data to accompany the input.
                    sly_data is intended not to be inserted into the chat stream.
        :return: The ChatRequest dictionary
        """
        # Set up a request
        chat_request = {
            "session_id": self.session_id,
            "user_message": {
                "type": 1,          # HUMAN from chat.proto
                "text": agent_input
            }
        }

        # At some point in the future we might want to block all
        # or parts of the sly_data from going to external agents.
        if sly_data is not None and len(sly_data.keys()) > 0:
            chat_request["sly_data"] = sly_data

        return chat_request

    async def delete_resources(self, parent_run_context: RunContext):
        """
        Cleans up after any allocated resources on their server side.
        :param parent_run_context: The RunContext which contains the scope
                    of operation of this CallableNode
        """
        self.session = None
        self.session_id = None
