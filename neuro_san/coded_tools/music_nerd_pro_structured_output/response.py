from typing import Any
from typing import Dict
from typing import Union

from neuro_san.interfaces.coded_tool import CodedTool


class Response(CodedTool):
    """
    A tool that return structured output to user
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates the passed running cost each time it's called.
        :param args: A dictionary with the following keys:
                    "answer": the answer to the user question.
                    "running_cost": the current running cost.

        :param sly_data: A dictionary containing parameters that should be kept out of the chat stream.
                         Keys expected for this implementation are:
                         None

        :return: A dictionary containing:
                "answer": the answer to the user query.
                "running_cost": the current running cost.
        """
        print("=================== Formating Response =====================")

        response = {
            "answer": args.get("answer"),
            "running_cost": args.get("running_cost")
        }

        return response

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)
