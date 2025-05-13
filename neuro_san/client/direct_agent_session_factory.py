
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
from neuro_san.internals.interfaces.context_type_toolbox_factory import ContextTypeToolboxFactory
from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.internals.interfaces.context_type_llm_factory import ContextTypeLlmFactory
from neuro_san.internals.run_context.factory.master_toolbox_factory import MasterToolboxFactory
from neuro_san.internals.run_context.factory.master_llm_factory import MasterLlmFactory
from neuro_san.internals.graph.persistence.agent_tool_registry_restorer import AgentToolRegistryRestorer
from neuro_san.internals.graph.persistence.registry_manifest_restorer import RegistryManifestRestorer
from neuro_san.internals.interfaces.agent_tool_factory_provider import AgentToolFactoryProvider
from neuro_san.internals.tool_factories.service_tool_factory_provider import ServiceToolFactoryProvider
from neuro_san.session.direct_agent_session import DirectAgentSession
from neuro_san.session.external_agent_session_factory import ExternalAgentSessionFactory
from neuro_san.session.session_invocation_context import SessionInvocationContext


class DirectAgentSessionFactory:
    """
    Sets up everything needed to use a DirectAgentSession more as a library.
    This includes:
        * Some reading of AgentToolRegistries
        * Setting up ServiceToolFactoryProvider with agent registries
          which were read in
        * Initializing an LlmFactory
    """

    def __init__(self):
        """
        Constructor
        """
        manifest_restorer = RegistryManifestRestorer()
        self.manifest_tool_registries: Dict[str, AgentToolRegistry] = manifest_restorer.restore()
        tool_factory: ServiceToolFactoryProvider =\
            ServiceToolFactoryProvider.get_instance()
        for agent_name, tool_registry in self.manifest_tool_registries.items():
            tool_factory.add_agent_tool_registry(agent_name, tool_registry)

    def create_session(self, agent_name: str, use_direct: bool = False,
                       metadata: Dict[str, str] = None) -> AgentSession:
        """
        :param agent_name: The name of the agent to use for the session.
                This name can be something in the manifest file (with no file suffix)
                or a specific full-reference to an agent network's hocon file.
        :param use_direct: When True, will use a Direct session for
                    external agents that would reside on the same server.
        :param metadata: A grpc metadata of key/value pairs to be inserted into
                         the header. Default is None. Preferred format is a
                         dictionary of string keys to string values.
        """

        tool_registry: AgentToolRegistry = self.get_agent_tool_registry(agent_name)

        llm_factory: ContextTypeLlmFactory = MasterLlmFactory.create_llm_factory()
        toolbox_factory: ContextTypeToolboxFactory = MasterToolboxFactory.create_toolbox_factory()
        # Load once now that we know what tool registry to use.
        # Include "agent_llm_info_file" from agent network hocon to llm factory.
        agent_llm_info_file = tool_registry.get_agent_llm_info_file()
        llm_factory.load(agent_llm_info_file)
        toolbox_factory.load()

        factory = ExternalAgentSessionFactory(use_direct=use_direct)
        invocation_context = SessionInvocationContext(factory, llm_factory, toolbox_factory, metadata)
        invocation_context.start()
        session: DirectAgentSession = DirectAgentSession(tool_registry=tool_registry,
                                                         invocation_context=invocation_context,
                                                         metadata=metadata)
        return session

    def get_agent_tool_registry(self, agent_name: str) -> AgentToolRegistry:
        """
        :param agent_name: The name of the agent whose AgentToolRegistry we want to get.
                This name can be something in the manifest file (with no file suffix)
                or a specific full-reference to an agent network's hocon file.
        :return: The AgentToolRegistry corresponding to that agent.
        """

        if agent_name is None or len(agent_name) == 0:
            return None

        tool_registry: AgentToolRegistry = None
        if agent_name.endswith(".hocon") or agent_name.endswith(".json"):
            # We got a specific file name
            restorer = AgentToolRegistryRestorer()
            tool_registry = restorer.restore(file_reference=agent_name)
        else:
            # Use the standard stuff available via the manifest file.
            tool_factory: ServiceToolFactoryProvider =\
                ServiceToolFactoryProvider.get_instance()
            tool_registry_provider: AgentToolFactoryProvider =\
                tool_factory.get_agent_tool_factory_provider(agent_name)
            tool_registry = tool_registry_provider.get_agent_tool_factory()

        return tool_registry
