
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

from neuro_san.internals.run_context.interfaces.async_agent_session_factory import AsyncAgentSessionFactory


class InvocationContext:
    """
    Class for encapsulating specific policy classes that pertain to
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

    def set_asyncio_executor(self, asyncio_executor: AsyncioExecutor):
        """
        :param asyncio_executor: The AsyncioExecutor to associate with the invocation
        """
        self.asyncio_executor = asyncio_executor
