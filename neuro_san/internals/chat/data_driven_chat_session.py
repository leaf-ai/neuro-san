
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
from typing import Iterator
from typing import List

import traceback

from datetime import datetime

from openai import BadRequestError

from neuro_san.internals.chat.async_collating_queue import AsyncCollatingQueue
from neuro_san.internals.chat.chat_session import ChatSession
from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.internals.graph.tools.front_man import FrontMan
from neuro_san.internals.interfaces.invocation_context import InvocationContext
from neuro_san.internals.journals.compatibility_journal import CompatibilityJournal
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.agent_framework_message import AgentFrameworkMessage
from neuro_san.internals.messages.chat_message_type import ChatMessageType
from neuro_san.internals.messages.message_utils import convert_to_chat_message
from neuro_san.internals.messages.message_utils import pretty_the_messages
from neuro_san.internals.run_context.factory.run_context_factory import RunContextFactory
from neuro_san.internals.run_context.interfaces.run_context import RunContext


# pylint: disable=too-many-instance-attributes
class DataDrivenChatSession(ChatSession):
    """
    ChatSession implementation that consolidates policy
    in using data-driven agent tool graphs.
    """

    def __init__(self, registry: AgentToolRegistry,
                 invocation_context: InvocationContext,
                 journal: Journal = None):
        """
        Constructor

        :param registry: The AgentToolRegistry to use.
        :param invocation_context: The context policy container that pertains to the invocation
                    of the agent.
        :param journal: The Journal that captures messages for user output
        """

        self.registry: AgentToolRegistry = registry
        self.front_man: FrontMan = None
        self.latest_response = None
        self.last_input_timestamp = datetime.now()
        self.sly_data: Dict[str, Any] = {}
        self.queue: AsyncCollatingQueue = AsyncCollatingQueue()
        self.last_streamed_index: int = 0
        self.invocation_context: InvocationContext = invocation_context

        self.journal: Journal = journal
        if journal is None:
            self.journal = CompatibilityJournal(self.queue)

    def get_queue(self) -> AsyncCollatingQueue:
        """
        :return: The AsyncCollatingQueue associated with this ChatSession instance.
        """
        return self.queue

    async def set_up(self):
        """
        Resets or sets the instance up for the first time.
        """
        # Reset the journal
        self.journal = CompatibilityJournal(self.queue)

        # Reset any sly data
        # This ends up being the one reference to the sly_data that gets passed around
        # to the graph components. Updating this updates everyone else.
        self.sly_data = {}

        # Reset what we might have created before.
        await self.delete_resources()

        run_context: RunContext = RunContextFactory.create_run_context(None, None,
                                                                       invocation_context=self.invocation_context)
        await self.journal.write("setting up chat agent(s)...", run_context.get_origin())

        self.front_man = self.registry.create_front_man(self.journal, self.sly_data, run_context)
        await self.front_man.create_resources()

    async def chat(self, user_input: str,
                   invocation_context: InvocationContext,
                   sly_data: Dict[str, Any] = None) -> Iterator[Dict[str, Any]]:
        """
        Main entry-point method for accepting new user input

        :param user_input: A string with the user's input
        :param invocation_context: The context policy container that pertains to the invocation
                    of the agent.
        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be None.
        :return: An Iterator over dictionary representation of chat messages.
                The keys/values/structure of these chat message dictionaries will reflect
                instances of ChatMessage from chat.proto.

                Note that Iterators themselves are *not* simply lists. They are a Python
                construct intended for use in a for-loop that is allowed to come up with
                its content dynamically.  For our purposes, when an initiator of chat()
                gets a handle to this Iterator, they can begin looping/waiting on its contents
                without the content itself having been created yet.  This is a building
                block of streaming results even though direct callers may not actually
                be streaming.

        Results are polled from get_latest_response() below, as this non-streaming
        version can take longer than the lifetime of a socket.
        """
        if self.front_man is None:
            await self.set_up()

        # Remember when we were last given input
        self.last_input_timestamp = datetime.now()

        # While deciding how to respond, there is no response yet
        self.clear_latest_response()

        # Update sly data, if any.
        # Note that since this instance is the owner of the sly_data,
        # any update here should get transmitted to all the other graph components
        # because it is expected they share the reference and only interact with it
        # in a read-only fashion.
        if sly_data is not None:
            self.sly_data.update(sly_data)

        try:
            await self.journal.write("consulting chat agent(s)...", self.front_man.run_context.get_origin())

            # DEF - drill further down for iterator from here to enable getting
            #       messages from downstream agents.
            raw_messages: List[Any] = await self.front_man.submit_message(user_input)

        except BadRequestError:
            # This can happen if the user is trying to send a new message
            # while it is still working on a previous message that has not
            # yet returned.
            raw_messages: List[Any] = [
                AgentFrameworkMessage(content="Patience, please. I'm working on it.")
            ]
            print(traceback.format_exc())

        # Update the polling response.
        prettied_messages = pretty_the_messages(raw_messages)
        self.latest_response = prettied_messages

        chat_messages: List[Dict[str, Any]] = []
        for raw_message in raw_messages:
            chat_message: Dict[str, Any] = convert_to_chat_message(raw_message, self.front_man.run_context.get_origin())
            chat_messages.append(chat_message)

        return iter(chat_messages)

    async def streaming_chat(self, user_input: str,
                             invocation_context: InvocationContext,
                             sly_data: Dict[str, Any] = None):
        """
        Main streaming entry-point method for accepting new user input

        :param user_input: A string with the user's input
        :param invocation_context: The context policy container that pertains to the invocation
                    of the agent.
        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be None.
        :return: Nothing.  Response values are put on a queue whose consumtion is
                managed by the Iterator aspect of AsyncCollatingQueue returned by get_queue().
        """
        # Queue Producer from this:
        #   https://stackoverflow.com/questions/74130544/asyncio-yielding-results-from-multiple-futures-as-they-arrive

        chat_messages: Iterator[Dict[str, Any]] = await self.chat(user_input, sly_data)
        message_list: List[Dict[str, Any]] = list(chat_messages)
        index: int = len(message_list) - 1
        chat_message: Dict[str, Any] = message_list[index]

        # The consumer await-s for self.queue.get()
        await self.queue.put(chat_message)
        self.last_streamed_index = index

        # Put an end-marker on the queue to tell the consumer we truly are done
        # and it doesn't need to wait for any more messages.
        await self.queue.put_final_item()

    def get_journal(self) -> Journal:
        """
        :return: The Journal which has been capturing all the "thinking" messages.
        """
        return self.journal

    def get_latest_response(self) -> str:
        """
        :return: The most recent response to the user from the chat agent.
                Can be None if the chat agent is still chewing on the previous user input.
        """
        return self.latest_response

    def clear_latest_response(self):
        """
        Clears out the latest response so as not to return duplicates.
        """
        self.latest_response = None

    async def delete_resources(self):
        """
        Frees up any service-side resources.
        """
        if self.front_man is not None:
            await self.front_man.delete_resources(None)
            self.front_man = None

    def get_last_input_timestamp(self) -> Any:
        """
        :return: The result of datetime.now() when the chat agent
                last received input.
        """
        return self.last_input_timestamp
