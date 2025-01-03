
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
from typing import List

from neuro_san.run_context.interfaces.run_context import RunContext


class CallableTool:
    """
    Interface describing what a CallingTool can access
    when invoking LLM function calls.
    """

    async def build(self) -> List[Any]:
        """
        Main entry point to the class.
        :return: A List of messages produced during this process.
        """
        raise NotImplementedError

    async def delete_resources(self, parent_run_context: RunContext):
        """
        Cleans up after any allocated resources on their server side.
        :param parent_run_context: The RunContext which contains the scope
                    of operation of this CallableNode
        """
        raise NotImplementedError
