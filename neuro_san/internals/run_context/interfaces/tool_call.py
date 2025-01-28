
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
