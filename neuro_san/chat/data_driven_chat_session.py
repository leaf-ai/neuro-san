
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
from typing import Iterator
from typing import List

import traceback

from asyncio.queues import Queue
from collections.abc import AsyncIterator
from datetime import datetime

from openai import BadRequestError

from neuro_san.chat.chat_session import ChatSession
from neuro_san.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.graph.tools.front_man import FrontMan
from neuro_san.utils.message_utils import convert_to_chat_message
from neuro_san.utils.message_utils import pretty_the_messages
from neuro_san.utils.agent_framework_message import AgentFrameworkMessage
from neuro_san.utils.stream_to_logger import StreamToLogger


# pylint: disable=too-many-instance-attributes
class DataDrivenChatSession(ChatSession):
    """
    ChatSession implementation that consolidates policy
    in using data-driven agent tool graphs.
    """

    def __init__(self, registry: AgentToolRegistry,
                 logger: StreamToLogger = None,
                 setup: bool = False):
        """
        Constructor

        :param registry: The AgentToolRegistry to use.
        :param logger: The StreamToLogger that captures messages for user output
        :param setup: Whether or not set_up() should be called
                    by the constructor. Default is False.
        """

        use_logger: StreamToLogger = logger
        if logger is None:
            use_logger = StreamToLogger()
        self.logger: StreamToLogger = use_logger

        self.registry: AgentToolRegistry = registry
        self.front_man: FrontMan = None
        self.latest_response = None
        self.last_input_timestamp = datetime.now()
        self.sly_data: Dict[str, Any] = {}
        self.queue: Queue[Dict[str, Any]] = Queue()
        self.last_streamed_index: int = 0

        if setup:
            self.set_up()

    async def set_up(self):
        """
        Resets or sets the instance up for the first time.
        """
        # Reset the logger
        self.logger = StreamToLogger()
        self.logger.write("setting up chat agent(s)...")

        # Reset any sly data
        # This ends up being the one reference to the sly_data that gets passed around
        # to the graph components. Updating this updates everyone else.
        self.sly_data = {}

        # Reset what we might have created before.
        await self.delete_resources()

        self.front_man = self.registry.create_front_man(self.logger, self.sly_data)
        await self.front_man.create_resources()

    async def chat(self, user_input: str, sly_data: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """
        Main entry-point method for accepting new user input

        :param user_input: A string with the user's input
        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be None.
        :return: An Iterator of chat.ChatMessage dictionaries

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
            self.logger.write("consulting chat agent(s)...")

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
            chat_message: Dict[str, Any] = convert_to_chat_message(raw_message)
            chat_messages.append(chat_message)

        return iter(chat_messages)

    async def streaming_chat(self, user_input: str, sly_data: Dict[str, Any]):
        """
        Main streaming entry-point method for accepting new user input

        :param user_input: A string with the user's input
        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be None.
        :return: Nothing.  Response values are put on a queue to be read by a call to queue_consumer()
        """
        # Queue Producer from this:
        #   https://stackoverflow.com/questions/74130544/asyncio-yielding-results-from-multiple-futures-as-they-arrive
        # DEF - These put()s will eventually be pushed down into the library.
        chat_messages: Iterator[Dict[str, Any]] = await self.chat(user_input, sly_data)
        for index, chat_message in enumerate(chat_messages):

            # For now filter what we send in the service.
            # This responsibility will eventually largely move to the client. 
            if self.is_streamable_message(chat_message, index):
                # The consumer await-s for self.queue.get()
                await self.queue.put(chat_message)
                self.last_streamed_index = index

        # Put an end-marker on the queue to tell the consumer we truly are done
        # and it doesn't need to wait for any more messages.
        end_dict = {"end": True}
        await self.queue.put(end_dict)

    def is_streamable_message(self, chat_message: Dict[str, Any], index: int) -> bool:
        """
        Filter chat messages from the full logs that are in/appropriate for streaming.

        :param chat_message: A Chat message dictionary of the form in chat.ChatMessage proto
        :param index: The place in the chat history the message has
        :return: True if the given message should be streamed back. False if not.
        """

        # This comes from definitions in chat.proto
        ai_message_type: int = 3

        message_type: int = chat_message.get("type")

        # Only report messages that are important enough to send back as part of chat
        # (for now).  This includes any response for an AI (read: LLM), a tool, or
        # agent or framework messages.
        if message_type is None or message_type < ai_message_type:
            return False

        if index <= self.last_streamed_index:
            return False

        return True

    async def queue_consumer(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Queue Consumer from this:
            https://stackoverflow.com/questions/74130544/asyncio-yielding-results-from-multiple-futures-as-they-arrive

        Loops until either the timeout is met or the end marker is seen.

        :return: An AsyncIterator over the messages from the agent(s).
        """
        done: bool = False
        while not done:
            try:
                # DEF - we once called asyncio.wait_for() here to get a timeout behavior.
                message: Dict[str, Any] = await self.queue.get()
                if not isinstance(message, Dict):
                    print(f"object on queue is of type {message.__class__.__name__}")
                    message = {"end": True}

                done = message.get("end") is not None
                if not done:
                    # yield all messages except the end marker
                    yield message

            except TimeoutError:
                print("Timeout in waiting to consume")
                done = True

    def get_logger(self) -> StreamToLogger:
        """
        :return: The StreamToLogger which has been capturing all the "thinking" messages.
        """
        return self.logger

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
