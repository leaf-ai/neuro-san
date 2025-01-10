from typing import Any
from typing import Dict
from typing import List
from typing import Union

import pandas as pd

from neuro_san.interfaces.coded_tool import CodedTool


class CodeValidator(CodedTool):
    """
    CodedTool implementation which handles validating a code snippet.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Called when the coded tool is invoked by the agent hierarchy.

        :param args: An argument dictionary whose keys are the parameters
                to the coded tool and whose values are the values passed for them
                by the calling agent.  This dictionary is to be treated as read-only.

                The argument dictionary expects the following keys:
                    "code_snippet":  Python code snippet to run for synthetic data generation.

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
                a dictionary containing S3 URI of resulting output,
                which includes the following key:
                    "output_url"
            otherwise:
                a text string an error message in the format:
                "Error: <error message>"
        """
        # Formulate the file reference for the request
        code_snippet = args.get("code_snippet")

        # Validate the code
        is_valid, error_message = self.validate_code(code_snippet)
        if not is_valid:
            return {"error": error_message}
        else:
            return {"code_snippet": code_snippet}

    # Function to validate matplotlib code
    def validate_code(self, code):
        try:
            # Check for unsafe imports or malicious code
            disallowed_imports = ["io", "os", "subprocess", "sys", "importlib", "pickle", "shutil", "tempfile"]
            for disallowed in disallowed_imports:
                if disallowed in code:
                    raise ValueError(f"Disallowed import detected: {disallowed}")
            compile(code, '<string>', 'exec')
            print("Code validation successful.")
        except (SyntaxError, ValueError) as e:
            print(f"Code validation failed: {e}")
            return False, str(e)
        return True, None
