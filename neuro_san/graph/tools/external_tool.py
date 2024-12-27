
# Copyright (C) 2023-2024 Cognizant Digital Business, Evolutionary AI.
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

import asyncio
import json

from neuro_san.journals.journal import Journal
from neuro_san.run_context.interfaces.callable_tool import CallableTool
from neuro_san.run_context.interfaces.run_context import RunContext
from neuro_san.run_context.utils.external_tool_adapter import ExternalToolAdapter
from neuro_san.session.agent_session import AgentSession


class ExternalTool(CallableTool):
    """
    CallableTool implementation that handles using a service to call
    another agent hierarchy as a tool.
    """

    DEFAULT_SLEEP_SECONDS: int = 5

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
                        ExternalToolAdapter.
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
        message_list: List[str] = []

        # Create an AgentSession if necessary
        if self.session is None:
            agent_location: Dict[str, str] = ExternalToolAdapter.parse_external_agent(self.agent_url)
            self.session = ExternalToolAdapter.create_session(agent_location)

        # Send off the input
        await self.send_input(f"```json\n{json.dumps(self.arguments)}```", self.sly_data)

        # Set up listening for the response
        logs_request = {
            "session_id": self.session_id
        }

        # Poll until we get a response.
        response: str = None
        while response is None or len(response) == 0:

            # We need to wait for a response.
            # Don't hog the executor.
            await asyncio.sleep(self.DEFAULT_SLEEP_SECONDS)

            # It'd be nice if there were an async version of this
            logs_response = self.session.logs(logs_request)

            # Right now we don't care about "logs" field in response.
            # Focus on a single answer for now.
            # We should also eventually care about the possibility
            # of a scaled-up agent service whose session id does
            # not exist on all replications of a single service pod.
            response = logs_response.get("chat_response")

        # Parse the logs response for the last thing the assistant said
        response_split: List[str] = response.split("assistant: ")
        content: str = response_split[-1]
        if len(response_split) < 2:
            # The assistant marker not being in the logs is a very uncommon situation,
            # but still it would be nice to have some idea of the frequency if it
            # actually does arise.  It's not really an error as far as we know.
            # Let the upstream agent figure it out for now until we know what to do.
            print(f"Response from {self.agent_url} contains no indentifying marker")

        # Prepare the output
        message: Dict[str, Any] = {
            "role": "assistant",
            "content": content
        }

        message_list.append(message)
        messages_str: str = json.dumps(message_list)

        return messages_str

    async def send_input(self, agent_input: str, sly_data: Dict[str, Any]):
        """
        Send input to the external agent
        :param agent_input: A single string to send as input to the agent
        :param sly_data: Any private sly_data to accompany the input.
                    sly_data is intended not to be inserted into the chat stream.
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

        # Send the request and get the session_id against which to query results.
        # It'd be nice if there were an async version of this
        chat_response = self.session.chat(chat_request)
        if self.session_id is None:
            self.session_id = chat_response.get("session_id")

    async def delete_resources(self, parent_run_context: RunContext):
        """
        Cleans up after any allocated resources on their server side.
        :param parent_run_context: The RunContext which contains the scope
                    of operation of this CallableNode
        """
        self.session = None
        self.session_id = None
