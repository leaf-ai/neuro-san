
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

from neuro_san.internals.graph.tools.calling_tool import CallingTool
from neuro_san.internals.interfaces.invocation_context import InvocationContext
from neuro_san.internals.run_context.interfaces.run import Run


class FrontMan(CallingTool):
    """
    A CallingTool implementation which is the root of the call graph.
    """

    async def submit_message(self, user_input: str) -> List[Any]:
        """
        Entry-point method for callers of the root of the Tool tree.

        :param user_input: An input string from the user.
        :return: A list of response messages for the run
        """
        # Initialize our return value
        decision_messages: List[Any] = []

        decision_run: Run = await self.run_context.submit_message(user_input)

        terminate = False
        while not terminate:
            if self.run_context is None:
                # Breaking from inside a container during cleanup can yield a None
                # run_context
                break

            decision_run = await self.run_context.wait_on_run(decision_run, self.journal)

            if decision_run.requires_action():
                decision_run = await self.make_tool_function_calls(decision_run)
            else:
                # Needs to get more information from the user on the basic task
                # of collecting information from the user about the decision.
                if self.run_context is None:
                    # Breaking from inside a container during cleanup can yield a None
                    # run_context
                    break
                decision_messages = await self.run_context.get_response()
                terminate = True

        return decision_messages

    def update_invocation_context(self, invocation_context: InvocationContext):
        """
        Update internal state based on the InvocationContext instance passed in.
        :param invocation_context: The context policy container that pertains to the invocation
        """
        self.journal = invocation_context.get_journal()
        if self.run_context is not None:
            self.run_context.update_invocation_context(invocation_context)

    async def build(self) -> List[Any]:
        """
        Main entry point to the class.

        :return: A List of messages produced during this process.
        """
        raise NotImplementedError
