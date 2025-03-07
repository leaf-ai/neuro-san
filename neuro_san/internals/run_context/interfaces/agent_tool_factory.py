
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
from typing import Any
from typing import Dict

from neuro_san.internals.run_context.interfaces.callable_tool import CallableTool
from neuro_san.internals.run_context.interfaces.run_context import RunContext


class AgentToolFactory:
    """
    Interface describing a factory that creates agent tools.
    Having this interface breaks some circular dependencies.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def create_agent_tool(self,
                          parent_run_context: RunContext,
                          parent_agent_spec: Dict[str, Any],
                          name: str,
                          sly_data: Dict[str, Any],
                          arguments: Dict[str, Any]) -> CallableTool:
        """
        Create an active node for an agent from its spec.

        :param parent_run_context: The RunContext of the agent calling this method
        :param parent_agent_spec: The spec of the agent calling this method.
        :param name: The name of the agent to get out of the registry
        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be an empty dictionary.
        :param arguments: A dictionary of arguments for the newly constructed agent
        :return: The CallableTool agent referred to by the name.
        """
        raise NotImplementedError

    def get_agent_tool_spec(self, name: str) -> Dict[str, Any]:
        """
        :param name: The name of the agent tool to get out of the registry
        :return: The dictionary representing the spec registered agent
        """
        raise NotImplementedError

    def get_config(self) -> Dict[str, Any]:
        """
        :return: The config dictionary given to the constructor.
        """
        raise NotImplementedError

    def get_agent_tool_path(self) -> str:
        """
        :return: The path under which tools for this registry should be looked for.
        """
        raise NotImplementedError

    def get_name_from_spec(self, agent_spec: Dict[str, Any]) -> str:
        """
        :param agent_spec: A single agent to register
        :return: The agent name as per the spec
        """
        raise NotImplementedError
