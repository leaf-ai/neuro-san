from typing import Any
from typing import Dict
from typing import List
from typing import Union

import pandas as pd

from neuro_san.interfaces.coded_tool import CodedTool


class DataDescriber(CodedTool):
    """
    CodedTool implementation which summarizes the DataFrame by returning the result of `df.describe(include='all')`
    as a JSON dictionary..
    """
    def __init__(self):
        self.default_path = "./neuro_san/coded_tools/analytics-san/credit_risk_data_20250109.csv"

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Called when the coded tool is invoked by the agent hierarchy.

        :param args: An argument dictionary whose keys are the parameters
                to the coded tool and whose values are the values passed for them
                by the calling agent.  This dictionary is to be treated as read-only.

                The argument dictionary expects the following keys:
                    "input_path": The input path to a CSV file

        :param sly_data: A dictionary whose keys are defined by the agent hierarchy,
                but whose values are meant to be kept out of the chat stream.

                This dictionary is largely to be treated as read-only.
                It is possible to add key/value pairs to this dict that do not
                yet exist as a bulletin board, as long as the responsibility
                for which coded_tool publishes new entries is well understood
                by the agent chain implementation and the coded_tool implementation
                adding the data is not invoke()-ed more than once.

                Keys expected for this implementation are:
                    None

        :return:
            In case of successful execution:
                a JSON dictionary describing the dataframe
            otherwise:
                a text string an error message in the format:
                "Error: <error message>"
        """
        # Formulate the file reference for the request
        # input_path = input("Provide path to the input CSV (to use a sample data, press enter): ")
        input_path = sly_data.get("input_path", self.default_path)

        df = pd.read_csv(file_path)
        # Get the summary statistics for both numerical and categorical features
        full_summary = df.describe(include='all').to_dict()
        
        return {"data_description": full_summary}
