
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

import uuid

from neuro_san.internals.run_context.interfaces.tool_call import ToolCall


class LangChainToolCall(ToolCall):
    """
    A LangChain implementation of a ToolCall

    For the uninitiated: A "ToolCall" in langchain/openai parlance is a *request*
    that a tool be called with certain structured function arguments.
    """

    def __init__(self, tool_name: str, args: Any, run_id: str):
        """
        Constructor

        :param tool_name: The name of the tool to be called
        :param args: The arguments the tool is requested to be called with
                So far we've only seen this as Dict[str, Any], but the langchain
                typing is Any, so we stick with that.
        :param run_id: The string id of the parent run so that the tool's
                    ids can be associated with that.
        """
        self.tool_name: str = tool_name
        self.args = args
        self.id: str = f"tool_call_{run_id}_{uuid.uuid4()}"

    def get_id(self) -> str:
        """
        :return: The string id of this run
        """
        return self.id

    def get_function_arguments(self) -> Dict[str, Any]:
        """
        :return: Returns a dictionary of the function arguments for the tool call
        """
        return self.args

    def get_function_name(self) -> str:
        """
        :return: Returns the string name of the tool
        """
        return self.tool_name
