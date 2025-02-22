
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

from leaf_common.asyncio.asyncio_executor import AsyncioExecutor

from neuro_san.internals.chat.async_collating_queue import AsyncCollatingQueue
from neuro_san.internals.interfaces.async_agent_session_factory import AsyncAgentSessionFactory
from neuro_san.internals.interfaces.invocation_context import InvocationContext
from neuro_san.internals.journals.compatibility_journal import CompatibilityJournal
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.origination import Origination


class SessionInvocationContext(InvocationContext):
    """
    Implementation of InvocationContext which encapsulates specific policy classes that pertain to
    a single invocation of an AgentSession, whether by way of a
    service call or library call.
    """

    def __init__(self, async_session_factory: AsyncAgentSessionFactory,
                 asyncio_executor: AsyncioExecutor = None,
                 metadata: Dict[str, str] = None):
        """
        Constructor

        :param async_session_factory: The AsyncAgentSessionFactory to use
                        when connecting with external agents.
        :param asyncio_executor: The AsyncioExecutor to use for running
                        stuff in the background asynchronously.
        :param metadata: A grpc metadata of key/value pairs to be inserted into
                         the header. Default is None. Preferred format is a
                         dictionary of string keys to string values.
        """

        self.async_session_factory: AsyncAgentSessionFactory = async_session_factory
        self.asyncio_executor: AsyncioExecutor = asyncio_executor
        self.origination: Origination = Origination()
        self.queue: AsyncCollatingQueue = AsyncCollatingQueue()
        self.journal: Journal = CompatibilityJournal(self.queue)
        self.metadata: Dict[str, str] = metadata
        self.request_reporting: Dict[str, Any] = {}

    def get_async_session_factory(self) -> AsyncAgentSessionFactory:
        """
        :return: The AsyncAgentSessionFactory associated with the invocation
        """
        return self.async_session_factory

    def get_asyncio_executor(self) -> AsyncioExecutor:
        """
        :return: The AsyncioExecutor associated with the invocation
        """
        return self.asyncio_executor

    def get_origination(self) -> Origination:
        """
        :return: The Origination instance carrying state about tool instantation
                during the course of the AgentSession.
        """
        return self.origination

    def get_journal(self) -> Journal:
        """
        :return: The Journal instance that allows message reporting
                during the course of the AgentSession.
        """
        return self.journal

    def get_queue(self) -> AsyncCollatingQueue:
        """
        :return: The AsyncCollatingQueue instance via which messages are streamed to the
                AgentSession mechanics
        """
        return self.queue

    def get_metadata(self) -> Dict[str, str]:
        """
        :return: The metadata to pass along with any request
        """
        return self.metadata

    def set_asyncio_executor(self, asyncio_executor: AsyncioExecutor):
        """
        :param asyncio_executor: The AsyncioExecutor to associate with the invocation
        """
        self.asyncio_executor = asyncio_executor

    def set_logs(self, logs: List[Any]):
        """
        :param logs: A list of strings corresponding to journal entries.
        """
        self.journal.set_logs(logs)

    def reset_origination(self):
        """
        Resets the origination
        """
        self.origination = Origination()

    def get_request_reporting(self) -> Dict[str, Any]:
        """
        :return: The request reporting dictionary
        """
        return self.request_reporting
