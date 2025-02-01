
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
                 asyncio_executor: AsyncioExecutor = None):
        """
        Constructor

        :param async_session_factory: The AsyncAgentSessionFactory to use
                        when connecting with external agents.
        :param asyncio_executor: The AsyncioExecutor to use for running
                        stuff in the background asynchronously.
        """

        self.async_session_factory: AsyncAgentSessionFactory = async_session_factory
        self.asyncio_executor: AsyncioExecutor = asyncio_executor
        self.origination: Origination = Origination()
        self.queue: AsyncCollatingQueue = AsyncCollatingQueue()
        self.journal: Journal = CompatibilityJournal(self.queue)

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

    def set_asyncio_executor(self, asyncio_executor: AsyncioExecutor):
        """
        :param asyncio_executor: The AsyncioExecutor to associate with the invocation
        """
        self.asyncio_executor = asyncio_executor
