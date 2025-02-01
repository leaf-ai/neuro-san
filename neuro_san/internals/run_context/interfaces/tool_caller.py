
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

from neuro_san.internals.run_context.interfaces.agent_spec_provider import AgentSpecProvider
from neuro_san.internals.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.internals.run_context.interfaces.run import Run


class ToolCaller(AgentSpecProvider):
    """
    Interface for Tools that call Agents/LLMs as functions.
    This is called by langchain Tools and implemented by CallingTool.
    """

    async def make_tool_function_calls(self, component_run: Run) -> Run:
        """
        Calls all of the callable_components' functions

        :param component_run: The Run which the component is operating under
        :return: A potentially updated Run for the component
        """
        raise NotImplementedError

    def get_factory(self) -> AgentToolFactory:
        """
        :return: The factory that contains the specs of all the tools
        """
        raise NotImplementedError

    def get_agent_tool_spec(self) -> Dict[str, Any]:
        """
        :return: the dictionary describing the data-driven agent
        """
        raise NotImplementedError

    def get_name(self) -> str:
        """
        :return: the name of the data-driven agent as it comes from the spec
        """
        raise NotImplementedError
