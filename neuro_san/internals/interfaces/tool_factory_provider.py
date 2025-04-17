
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

from neuro_san.internals.interfaces.agent_tool_factory_provider import AgentToolFactoryProvider


class ToolFactoryProvider:
    """
    Abstract interface for getting agent-specific tool factory providers
    """

    def get_agent_tool_factory_provider(self, agent_name: str) -> AgentToolFactoryProvider:
        """
        Get tool factory provider for given agent.
        :param agent_name: name of an agent
        :return: tool factory provider for this agent,
                 or None if no such provider is available.
        """
        raise NotImplementedError
