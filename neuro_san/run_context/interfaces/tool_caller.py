from typing import Any
from typing import Dict

from neuro_san.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.run_context.interfaces.run import Run


class ToolCaller:
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
