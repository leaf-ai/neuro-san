from typing import List

from neuro_san.run_context.interfaces.tool_call import ToolCall


class Run:
    """
    An interface describing a run of an assistant.
    """

    def get_id(self) -> str:
        """
        :return: The string id of this run
        """
        raise NotImplementedError

    def requires_action(self) -> bool:
        """
        :return: True if the status of the run requires external action.
                 False otherwise
        """
        raise NotImplementedError

    def get_tool_calls(self) -> List[ToolCall]:
        """
        :return: A list of ToolCalls.
        """
        raise NotImplementedError

    def model_dump_json(self) -> str:
        """
        :return: This object as a JSON string
        """
        raise NotImplementedError
