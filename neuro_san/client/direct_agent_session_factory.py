
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
from typing import Dict

from leaf_common.asyncio.asyncio_executor import AsyncioExecutor

from neuro_san.internals.graph.persistence.registry_manifest_restorer import RegistryManifestRestorer
from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.internals.run_context.interfaces.invocation_context import InvocationContext
from neuro_san.session.agent_session import AgentSession
from neuro_san.session.chat_session_map import ChatSessionMap
from neuro_san.session.direct_agent_session import DirectAgentSession
from neuro_san.session.external_agent_session_factory import ExternalAgentSessionFactory


# pylint: disable=too-few-public-methods
class DirectAgentSessionFactory:
    """
    Sets up everything needed to use a DirectAgentSession more as a library.
    This includes:
        * a ChatSessionMap
        * an AsyncioExecutor
        * Some reading of AgentToolRegistries
    """

    def __init__(self):
        """
        Constructor
        """
        self.asyncio_executor: AsyncioExecutor = AsyncioExecutor()
        init_arguments = {
            "chat_sessions": {},
            "executor": self.asyncio_executor
        }
        self.chat_session_map: ChatSessionMap = ChatSessionMap(init_arguments)

        manifest_restorer = RegistryManifestRestorer()
        self.manifest_tool_registries: Dict[str, AgentToolRegistry] = manifest_restorer.restore()

        self.asyncio_executor.start()

    def create_session(self, agent_name: str, use_direct: bool = False) -> AgentSession:
        """
        :param agent_name: The name of the agent to use for the session.
        :param use_direct: When True, will use a Direct session for
                    external agents that would reside on the same server.
        """

        factory = ExternalAgentSessionFactory(use_direct=use_direct)
        tool_registry: AgentToolRegistry = factory.get_tool_registry(agent_name, self.manifest_tool_registries)

        invocation_context = InvocationContext(factory, self.asyncio_executor)
        session: DirectAgentSession = DirectAgentSession(chat_session_map=self.chat_session_map,
                                                         tool_registry=tool_registry,
                                                         invocation_context=invocation_context)
        return session
