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

from neuro_san.internals.interfaces.agent_tool_factory_provider import AgentToolFactoryProvider
from neuro_san.internals.run_context.interfaces.agent_tool_factory import AgentToolFactory


class SingleAgentToolFactoryProvider(AgentToolFactoryProvider):
    """
    Class providing current agent tool factory for a given agent
    in the service scope.
    """
    def __init__(self, agent_name: str, agents_table: Dict[str, AgentToolFactory]):
        """
        Constructor.
        :param agent_name: name of an agent to provide AgentToolFactory instances for;
        :param agents_table: service-wide table mapping agent names to their
            currently active AgentToolFactory instances.
            This table is assumed to be dynamically modified outside a single agent scope.
        """
        self.agent_name = agent_name
        self.agents_table: Dict[str, AgentToolFactory] = agents_table

    def get_agent_tool_factory(self) -> AgentToolFactory:
        """
        Return current Agent tool factory instance for specific agent name.
        """
        return self.agents_table.get(self.agent_name, None)
