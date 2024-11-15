from typing import Any
from typing import List

from neuro_san.graph.tools.calling_tool import CallingTool
from neuro_san.run_context.interfaces.run import Run


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
            decision_run = await self.run_context.wait_on_run(decision_run, self.logger)
            self.logger.show_json(decision_run)

            if decision_run.requires_action():
                # This call is made when the decision assistant has scoped the
                # problem and knows the CAO. It's first task then is to set up
                # and call a prescriptor and pass it the CAO definitions as well
                # as the values for the Context attributes. The prescriptor,
                # in turn, will set up and call one or more predictors in its
                # process of working out what the values of the actions should be,
                # before it returns those values to the Decision Assistant.
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
