
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

from neuro_san.internals.run_context.interfaces.agent_tool_factory import AgentToolFactory


class AgentToolFactoryProvider:
    """
    Abstract interface for providing an agent tool factory at run-time.
    """
    def get_agent_tool_factory(self) -> AgentToolFactory:
        """
        Get tool factory provider for an agent.
        :return: tool factory for this agent,
                 or None if no such tool factory is available.
        """
        raise NotImplementedError
