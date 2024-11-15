from typing import Any
from typing import Dict


class ToolCall:
    """
    An interface representing a call to a tool
    """

    def get_id(self) -> str:
        """
        :return: The string id of this run
        """
        raise NotImplementedError

    def get_function_arguments(self) -> Dict[str, Any]:
        """
        :return: Returns a dictionary of the function arguments for the tool call
        """
        raise NotImplementedError

    def get_function_name(self) -> str:
        """
        :return: Returns the string name of the tool
        """
        raise NotImplementedError
