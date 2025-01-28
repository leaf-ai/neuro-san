
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
from typing import List

from neuro_san.internals.run_context.interfaces.tool_call import ToolCall


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
