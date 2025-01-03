
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

import json

from openai.types.beta.threads.required_action_function_tool_call \
    import Function
from openai.types.beta.threads.required_action_function_tool_call \
    import RequiredActionFunctionToolCall

from neuro_san.internals.run_context.interfaces.tool_call import ToolCall


class OpenAIToolCall(ToolCall):
    """
    An OpenAI implementation for ToolCall.
    """

    def __init__(self, tool_call: RequiredActionFunctionToolCall):
        """
        Constructor
        :param tool_call: The OpenAI RequiredActionFunctionToolCall on which this
                          implementation is based.
        """
        self.tool_call = tool_call

    def get_id(self) -> str:
        """
        :return: The string id of this run
        """
        return self.tool_call.id

    def get_function_arguments(self) -> Dict[str, Any]:
        """
        :return: Returns a dictionary of the function arguments for the tool call
        """
        function: Function = self.tool_call.function
        arguments: str = function.arguments

        function_arguments: Dict[str, Any] = json.loads(arguments)

        return function_arguments

    def get_function_name(self) -> str:
        """
        :return: Returns the string name of the tool
        """
        function: Function = self.tool_call.function
        return function.name
