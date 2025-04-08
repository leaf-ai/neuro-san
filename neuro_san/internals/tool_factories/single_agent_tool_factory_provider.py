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
from typing import Dict

from neuro_san.internals.interfaces.agent_tool_factory_provider import AgentToolFactoryProvider
from neuro_san.internals.run_context.interfaces.agent_tool_factory import AgentToolFactory

class SingleAgentToolFactoryProvider(AgentToolFactoryProvider):
    """
    Class providing current agent tool factory for a given agent
    in the service scope.
    """
    def __init__(self, agent_name: str, agents_table: Dict[str, AgentToolFactory]):
        self.agent_name = agent_name
        self.agents_table: Dict[str, AgentToolFactory] = agents_table

    def get_agent_tool_factory(self) -> AgentToolFactory:
        return self.agents_table.get(self.agent_name, None)
