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
from typing import Dict
from typing import List

from neuro_san.internals.interfaces.tool_factory_provider import ToolFactoryProvider
from neuro_san.internals.interfaces.agent_state_listener import AgentStateListener
from neuro_san.internals.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.internals.tool_factories.single_agent_tool_factory_provider import SingleAgentToolFactoryProvider


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

    def add_listener(self, listener: AgentStateListener):
        """
        Add a state listener to be notified when status of service agents changes.
        """
        self.listeners.append(listener)

    def remove_listener(self, listener: AgentStateListener):
        """
        Remove a state listener from registered set.
        """
        if listener in self.listeners:
            self.listeners.remove(listener)

    def add_agent_tool_registry(self, agent_name: str, registry: AgentToolFactory):
        """
        This method is a single point of entry in the service
        where we register a new "agent name + AgentToolFactory" pair in the service scope
        or notify the service that for existing agent its AgentToolFactory has been modified.
        """
        is_new: bool = False
        with self.lock:
            is_new = self.agents_table.get(agent_name, None) is None
            self.agents_table[agent_name] = registry
        # Notify listeners about this state change:
        # do it outside of internal lock
        for listener in self.listeners:
            if is_new:
                listener.agent_added(agent_name)
                self.logger.info("ADDED tool registry for agent %s", agent_name)
            else:
                listener.agent_modified(agent_name)
                self.logger.info("REPLACED tool registry for agent %s", agent_name)

    def setup_tool_registries(self, registries: Dict[str, AgentToolFactory]):
        """
        Replace agents registries with "registries" collection.
        Previous state could be empty.
        """
        prev_agents: Dict[str, AgentToolFactory] = {}
        with self.lock:
            prev_agents = self.agents_table
            self.agents_table = {}
        # Notify listeners that previous set of agents is removed
        for agent_name, _ in prev_agents.items():
            for listener in self.listeners:
                listener.agent_removed(agent_name)
        # Add the new agent+registry pairs
        for agent_name, tool_registry in registries.items():
            self.add_agent_tool_registry(agent_name, tool_registry)

    def remove_agent_tool_registry(self, agent_name: str):
        """
        Remove agent name and its AgentToolFactory from service scope,
        so that agent becomes unavailable on our server.
        """
        with self.lock:
            self.agents_table.pop(agent_name, None)
        # Notify listeners about this state change:
        # do it outside of internal lock
        for listener in self.listeners:
            listener.agent_removed(agent_name)
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
