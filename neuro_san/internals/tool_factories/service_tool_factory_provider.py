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

import logging
import threading
from typing import Any
from typing import Dict
from typing import List

from neuro_san.internals.interfaces.tool_factory_provider import ToolFactoryProvider
from neuro_san.internals.interfaces.agent_state_listener import AgentStateListener
from neuro_san.internals.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.internals.tool_factories.single_agent_tool_factory_provider import SingleAgentToolFactoryProvider
from neuro_san.internals.graph.persistence.agent_tool_registry_restorer import AgentToolRegistryRestorer


class ServiceToolFactoryProvider(ToolFactoryProvider):
    """
    Service-wide provider of agents tools factories.
    This class is a global singleton containing
    a table of currently active tool factories for each agent registered to the service.
    Note: a mapping from an agent to its tools factory is dynamic,
    as we can change agents definitions at service run-time.
    """

    instance = None

    def __init__(self):
        self.agents_table: Dict[str, AgentToolFactory] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.lock = threading.Lock()
        self.listeners: List[AgentStateListener] = []

    @classmethod
    def get_instance(cls):
        """
        Get a singleton instance of this class
        """
        if not ServiceToolFactoryProvider.instance:
            ServiceToolFactoryProvider.instance = ServiceToolFactoryProvider()
        return ServiceToolFactoryProvider.instance

    def add_state_listener(self, listener: AgentStateListener):
        """
        Add a state listener to be notified when status of service agents changes.
        """
        self.listeners.append(listener)

    def build_agent_tool_registry(self, agent_name: str, config: Dict[str, Any]):
        """
        Build agent tool registry from its configuration dictionary
        and register it for given agent name.
        """
        registry: AgentToolFactory = AgentToolRegistryRestorer().restore_from_config(agent_name, config)
        self.add_agent_tool_registry(agent_name, registry)

    def add_agent_tool_registry(self, agent_name: str, registry: AgentToolFactory):
        """
        Register existing agent tool registry
        """
        with self.lock:
            is_new: bool = self.agents_table.get(agent_name, None) is None
            self.agents_table[agent_name] = registry
            if is_new:
                self.logger.info("BUILT tool registry for agent %s", agent_name)
            else:
                self.logger.info("REPLACED tool registry for agent %s", agent_name)

    def remove_agent_tool_registry(self, agent_name: str):
        """
        Remove agent tool registry from the table
        """
        with self.lock:
            self.agents_table.pop(agent_name, None)
            self.logger.info("REMOVED tool registry for agent %s", agent_name)

    def get_agent_tool_factory_provider(self, agent_name: str) -> ToolFactoryProvider:
        """
        Get agent tool factory provider for a specific agent
        :param agent_name: name of an agent
        """
        return SingleAgentToolFactoryProvider(agent_name, self.agents_table)

    def get_agent_names(self) -> List[str]:
        """
        Return static list of agent names.
        """
        with self.lock:
            # Create static snapshot of agents names collection
            return list(self.agents_table.keys())
