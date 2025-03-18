
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

from neuro_san.interfaces.agent_session import AgentSession
from neuro_san.internals.interfaces.context_type_llm_factory import ContextTypeLlmFactory
from neuro_san.internals.run_context.langchain.default_llm_factory import DefaultLlmFactory
from neuro_san.internals.graph.persistence.registry_manifest_restorer import RegistryManifestRestorer
from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.session.direct_agent_session import DirectAgentSession
from neuro_san.session.external_agent_session_factory import ExternalAgentSessionFactory
from neuro_san.session.session_invocation_context import SessionInvocationContext


class DirectAgentSessionFactory:
    """
    Sets up everything needed to use a DirectAgentSession more as a library.
    This includes:
        * Some reading of AgentToolRegistries
        * Initializing an LlmFactory
    """

    def __init__(self):
        """
        Constructor
        """
        manifest_restorer = RegistryManifestRestorer()
        self.manifest_tool_registries: Dict[str, AgentToolRegistry] = manifest_restorer.restore()

    def create_session(self, agent_name: str, use_direct: bool = False,
                       metadata: Dict[str, str] = None) -> AgentSession:
        """
        :param agent_name: The name of the agent to use for the session.
        :param use_direct: When True, will use a Direct session for
                    external agents that would reside on the same server.
        :param metadata: A grpc metadata of key/value pairs to be inserted into
                         the header. Default is None. Preferred format is a
                         dictionary of string keys to string values.
        """

        factory = ExternalAgentSessionFactory(use_direct=use_direct)
        tool_registry: AgentToolRegistry = factory.get_tool_registry(agent_name, self.manifest_tool_registries)

        # Not happy that this goes direct to langchain implementation,
        # but can fix that with next LlmFactory extension.
        llm_factory: ContextTypeLlmFactory = DefaultLlmFactory()
        # Load once now that we know what tool registry to use.
        llm_factory.load()

        invocation_context = SessionInvocationContext(factory, llm_factory, metadata)
        invocation_context.start()
        session: DirectAgentSession = DirectAgentSession(tool_registry=tool_registry,
                                                         invocation_context=invocation_context,
                                                         metadata=metadata)
        return session
