from typing import List

from openai.types.beta.threads.run import Run as APIRun

from neuro_san.run_context.interfaces.run import Run
from neuro_san.run_context.interfaces.tool_call import ToolCall
from neuro_san.run_context.openai.openai_tool_call import OpenAIToolCall


class OpenAIRun(Run):
    """
    An OpenAI implementation of a Run of an assistant.
    """

    def __init__(self, openai_run: APIRun):
        """
        Constructor

        :param openai_run: The OpenAI Run on which this implementation is based
        """
        self.openai_run = openai_run

    def get_id(self) -> str:
        """
        :return: The string id of this run
        """
        return self.openai_run.id

    def requires_action(self) -> bool:
        """
        :return: True if the status of the run requires external action.
                 False otherwise
        """
        return self.openai_run.status == "requires_action"

    def is_running(self) -> bool:
        """
        :return: True if the run is in progress. False otherwise
        """
        return self.openai_run.status in ("queued", "in_progress")

    def get_tool_calls(self) -> List[ToolCall]:
        """
        :return: A list of ToolCalls.
        """
        tool_calls: List[ToolCall] = []

        openai_tool_calls = self.openai_run.required_action.submit_tool_outputs.tool_calls
        for openai_tool_call in openai_tool_calls:
            tool_call = OpenAIToolCall(openai_tool_call)
            tool_calls.append(tool_call)

        return tool_calls

    def model_dump_json(self) -> str:
        """
        :return: This object as a JSON string
        """
        return self.openai_run.model_dump_json()
