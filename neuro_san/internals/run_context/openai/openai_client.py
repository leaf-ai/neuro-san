
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
import os

from typing import Any
from typing import Dict
from typing import List

import logging

from openai import OpenAI
from openai import AsyncOpenAI
from openai.types.beta import Assistant
from openai.types.beta import Thread
from openai.types.beta.threads import Run
from openai.types.beta.thread_create_and_run_params import ThreadMessage


class OpenAIClient:
    """
    Implementation of different interfaces for using direct OpenAI calls.
    """

    def __init__(self, client: OpenAI = None, asynchronous: bool = False):
        """
        Constructor

        :param client: The OpenAI Client
        :param asynchronous: Boolean that says whether or not to use an asynchronous
                    OpenAI client.  Default is False.
        """
        if client is None:

            # 3 clients are needed at least, otherwise a down-chain agent
            # can't make multiple calls to its down-chain
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key is None:
                raise ValueError("ERROR: Missing OPENAI_API_KEY environment variable.")

            if asynchronous:
                client = AsyncOpenAI(api_key=api_key)
            else:
                client = OpenAI(api_key=api_key)

        self.client = client
        self.logger = logging.getLogger(self.__class__.__name__)

    def is_async(self):
        """
        :return: True is the underlying client is asynchronous.
                 False otherwise
        """
        return isinstance(self.client, AsyncOpenAI)

    async def create_run(self, thread_id: str, assistant_id: str) -> Run:
        """
        Notes: Used in langchain's OpenAIAssistantRunnable.invoke()
                Runs do not have to be deleted.
        :param thread_id:
        :param assistant_id:
        :return: A run
        """
        # Makes a POST to /threads/{thread_id}/runs
        if self.is_async():
            run: Run = await self.client.beta.threads.runs.create(thread_id=thread_id,
                                                                  assistant_id=assistant_id)
        else:
            run: Run = self.client.beta.threads.runs.create(thread_id=thread_id,
                                                            assistant_id=assistant_id)
        return run

    async def submit_tool_outputs(self, thread_id: str, run_id: str, tool_outputs: List[Any]) -> Run:
        """
        Notes: Used in langchain's OpenAIAssistantRunnable.invoke()
        :param thread_id:
        :param run_id:
        :param tool_outputs: Really a run_submit_tool_outputs_params.ToolOutput
        :return: A run
        """
        # Makes a POST to /threads/{thread_id}/runs/{run_id}/submit_tool_outputs
        if self.is_async():
            run: Run = await self.client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                                               run_id=run_id,
                                                                               tool_outputs=tool_outputs)
        else:
            run: Run = self.client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id,
                                                                         run_id=run_id,
                                                                         tool_outputs=tool_outputs)
        return run

    async def retrieve(self, thread_id: str, run_id: str) -> Run:
        """
        Notes: Used in langchain's OpenAIAssistantRunnable.invoke()
        :param thread_id:
        :param run_id:
        :return: A run
        """
        # Makes a GET to /threads/{thread_id}/runs/{run_id}
        if self.is_async():
            run: Run = await self.client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                                    run_id=run_id)
        else:
            run: Run = self.client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                              run_id=run_id)
        return run

    async def list_runs(self, thread_id: str) -> List[Any]:
        """
        :param thread_id:
        :return: A list of runs
        """
        if self.is_async():
            results = await self.client.beta.threads.runs.list(thread_id)
        else:
            results = self.client.beta.threads.runs.list(thread_id)
        return results.data

    async def create_thread(self) -> Thread:
        """
        Note: create_thread_and_run() is used in invoke()
        :return: A thread
        """
        # Makes a POST to /threads
        if self.is_async():
            thread: Thread = await self.client.beta.threads.create()
        else:
            thread: Thread = self.client.beta.threads.create()
        return thread

    async def delete_thread(self, thread_id: str):
        """
        :param thread_id: Thread id
        :return: Nothing
        """
        if self.is_async():
            await self.client.beta.threads.delete(thread_id)
        else:
            self.client.beta.threads.delete(thread_id)
        self.logger.info("Deleted thread_id %s", thread_id)

    async def create_message(self, thread_id: str, role: str, content: str) -> ThreadMessage:
        """
        Used in invoke()
        Messages do not have to be deleted
        :param thread_id: Thread id
        :param role: ???
        :param content: ???
        """
        thread_message: ThreadMessage = None

        # Makes a POST to /threads/{thread_id}/messages
        if self.is_async():
            thread_message = \
                    await self.client.beta.threads.messages.create(thread_id=thread_id,
                                                                   role=role,
                                                                   content=content)
        else:
            thread_message = \
                self.client.beta.threads.messages.create(thread_id=thread_id,
                                                         role=role,
                                                         content=content)
        return thread_message

    async def list_messages(self, thread_id: str, order: str = "asc") -> List[ThreadMessage]:
        """
        Used in invoke()
        :param thread_id: Thread id
        :param order: optional string describing the order of the messages
        :return: A list of messages (type?)
        """
        # Makes a GET to /threads/{thread_id}/messages
        if self.is_async():
            tuples = await self.client.beta.threads.messages.list(thread_id=thread_id, order=order)

            # The async API does not return a list of ThreadMessages, but instead a list
            # of Tuples.
            messages = []
            for one_tuple in tuples:
                # It has been observed empirically that the "data" tuple
                # contains a list of ThreadMessages
                if one_tuple[0] == "data":
                    message_list = one_tuple[1]
                    for message in message_list:
                        messages.append(message)
        else:
            messages = self.client.beta.threads.messages.list(thread_id=thread_id, order=order)

        return list(messages)

    async def create_assistant(self, name: str, instructions: str, model: str) -> Assistant:
        """
        used in OpenAIAssistantRunnable.create_assistant()
        :param name: string? name for the assistant
        :param instructions: ?
        :param model: ?
        :return: An assistant
        """
        # Makes a POST to /assistants
        assistant: Assistant = None
        if self.is_async():
            assistant = await self.client.beta.assistants.create(name=name,
                                                                 instructions=instructions,
                                                                 model=model)
        else:
            assistant = self.client.beta.assistants.create(name=name,
                                                           instructions=instructions,
                                                           model=model)
        return assistant

    async def update_assistant(self, assistant_id: str, tools: List[Dict[str, Any]]) -> Assistant:
        """
        Not used in langchain!
        :param assistant_id: The id of the assistant
        :param tools: A list of tools dictionaries?  (assistant_update_params.Tool)
        :return: An assistant
        """
        # Makes a POST to /assistants/{assistant_id}
        if self.is_async():
            assistant: Assistant = await self.client.beta.assistants.update(assistant_id=assistant_id,
                                                                            tools=tools)
        else:
            assistant: Assistant = self.client.beta.assistants.update(assistant_id=assistant_id,
                                                                      tools=tools)
        return assistant

    async def list_assistants(self) -> List[Assistant]:
        """
        :return: A list of assistants in use
        """
        if self.is_async():
            results = await self.client.beta.assistants.list()
        else:
            results = self.client.beta.assistants.list()
        return results.data

    async def delete_assistant(self, assistant_id: str):
        """
        :param assistant_id: The id of the assistant
        """
        if self.is_async():
            await self.client.beta.assistants.delete(assistant_id=assistant_id)
        else:
            self.client.beta.assistants.delete(assistant_id=assistant_id)
        self.logger.info("Deleted assistant_id %s", assistant_id)
