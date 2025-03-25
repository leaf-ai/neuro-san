from typing import Any
from typing import Dict

from neuro_san.interfaces.coded_tool import CodedTool


class AccountingAPI(CodedTool):
    """
    A tool that updates a running cost each time it is called.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates the passed running cost each time it's called.
        :param args: A dictionary with the following keys:
                    "running_cost": the running cost to update.

        :param sly_data: A dictionary containing parameters that should be kept out of the chat stream.
                         Keys expected for this implementation are:
                         None

        :return: A dictionary containing:
                 "running_cost": the updated running cost.
        """
        tool_name = self.__class__.__name__
        print(f"========== Calling {tool_name} ==========")
        # Parse the arguments
        print(f"args: {args}")
        running_cost: float = float(args.get("running_cost"))

        # Increment the running cost
        updated_running_cost: float = running_cost + 1.0

        tool_response = {
            "running_cost": updated_running_cost
        }
        print("-----------------------")
        print(f"{tool_name} response: ", tool_response)
        print(f"========== Done with {tool_name} ==========")
        return tool_response


# Example usage:
if __name__ == "__main__":
    an_accountant = AccountingAPI()
    # Initial running cost
    a_running_cost = 0.0
    a_response_1 = an_accountant.invoke(args={"running_cost": a_running_cost}, sly_data={})
    an_updated_running_cost = a_response_1["running_cost"]
    print(f"Updated running cost: {an_updated_running_cost}")
    a_response_2 = an_accountant.invoke(args={"running_cost": an_updated_running_cost}, sly_data={})
    an_updated_running_cost = a_response_2["running_cost"]
    print(f"Updated running cost: {an_updated_running_cost}")
