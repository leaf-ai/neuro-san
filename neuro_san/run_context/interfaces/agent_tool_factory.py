from typing import Any
from typing import Dict

from neuro_san.run_context.interfaces.callable_tool import CallableTool
from neuro_san.run_context.interfaces.run_context import RunContext
from neuro_san.utils.stream_to_logger import StreamToLogger


class AgentToolFactory:
    """
    Interface describing a factory that creates agent tools.
    Having this interface breaks some circular dependencies.
    """

    # pylint: disable=too-many-arguments
    def create_agent_tool(self,
                          parent_run_context: RunContext,
                          logger: StreamToLogger,
                          name: str,
                          sly_data: Dict[str, Any],
                          arguments: Dict[str, Any]) -> CallableTool:
        """
        :param name: The name of the agent to get out of the registry
        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be an empty dictionary.
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
