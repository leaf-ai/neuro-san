
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
from os import environ
from typing import Dict

from leaf_common.asyncio.asyncio_executor import AsyncioExecutor

from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.service.registry_manifest_restorer import RegistryManifestRestorer
from neuro_san.session.agent_session import AgentSession
from neuro_san.session.chat_session_map import ChatSessionMap
from neuro_san.session.direct_agent_session import DirectAgentSession


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

    def create_session(self, agent_name: str) -> AgentSession:
        """
        :param agent_name: The name of the agent to use for the session.
        """
        tool_registry: AgentToolRegistry = self.manifest_tool_registries.get(agent_name)
        if tool_registry is None:
            message = f"""
Agent named "{agent_name}" not found in manifest file: {environ.get("AGENT_MANIFEST_FILE")}.

Some things to check:
1. If the manifest file named above is None, know that the default points
   to the one provided with the neuro-san library for a smoother out-of-box
   experience.  If the agent you wanted is not part of that standard distribution,
   you need to set the AGENT_MANIFEST_FILE environment variable to point to a
   manifest.hocon file associated with your own project(s).
2. Check that the environment variable AGENT_MANIFEST_FILE is pointing to
   the manifest.hocon file that you expect and has no typos.
3. Does your manifest.hocon file contain a key for the agent specified?
4. Does the value for the key in the manifest file have a value of 'true'?
5. Does your agent name have a typo either in the hocon file or on the command line?
"""
            raise ValueError(message)

        session: DirectAgentSession = DirectAgentSession(self.chat_session_map,
                                                         tool_registry,
                                                         self.asyncio_executor)
        return session
