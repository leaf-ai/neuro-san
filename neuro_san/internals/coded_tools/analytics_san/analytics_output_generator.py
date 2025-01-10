import time
from typing import Any
from typing import Dict
from typing import List
from typing import Union

import uuid

from datetime import datetime
from urllib.parse import quote

from neuro_san.interfaces.coded_tool import CodedTool
from neuro_san.internals.coded_tools.analytics_san.grpc_task_client import GRPCTaskClient

class AnalyticsOutputGenerator(CodedTool):
    """
    CodedTool implementation which handles generating data plot
    from provided Python code
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: An argument dictionary whose keys are the parameters
                to the coded tool and whose values are the values passed for them
                by the calling agent.  This dictionary is to be treated as read-only.

                The argument dictionary expects the following keys:
                    "code" A string containing well-formed Python code segment;
                    "target" A string with S3 full destination path for code execution result
                             (like s3://my-bucket/my-plot.png)

        :param sly_data: A dictionary whose keys are defined by the agent hierarchy,
                but whose values are meant to be kept out of the chat stream.

                This dictionary is largely to be treated as read-only.
                It is possible to add key/value pairs to this dict that do not
                yet exist as a bulletin board, as long as the responsibility
                for which coded_tool publishes new entries is well understood
                by the agent chain implementation and the coded_tool implementation
                adding the data is not invoke()-ed more than once.

                Keys expected for this implementation are:
                    "login" The user id describing who is making the request.

        :return:
            In case of successful execution:
                a dictionary containing task execution status,
                which includes the following key:
                    "status"
            otherwise:
                a text string an error message in the format:
                "Error: <error message>"
        """
        print(f"ARGS: {args}")
        code_source: str = args.get("code", "")
        if not code_source:
            print("NO code string provided!")
            return "Error: NO CODE"
        target: str = args.get("target", "")
        if not target:
            print("NO destination path provided!")
            return "Error: NO DESTINATION PATH"

        service_endpoint: str = "localhost:30012"
        client = GRPCTaskClient(service_endpoint)

        task_id: str = f"task-{uuid.uuid4()}"
        dest_uri: str = target
        if dest_uri is None:
            dest_uri = f"s3://asd-test01/{task_id}/result.csv"

        # Construct dataset generation request:
        request_dict: Dict[str, Any] = \
            {
                "task_id": task_id,
                "code_source": code_source,
                "destination_uri": dest_uri,
                "params": {}
            }

        # Run task execution request:
        result = client.generate_dataset(request_dict)
        print(f"TASK RESULT: {result}")

        status_request: Dict[str, Any] = {"task_id": task_id}

        status: str = "TASK_RUNNING"
        while status == "TASK_RUNNING":
            result = client.get_task_status(status_request)
            status = result.get("status", "TASK_UNKNOWN")
            error_msg: str = result.get("error_msg", "")

        print(f"Task {task_id} done with status: {status} error: {error_msg}")

        if error_msg:
            return f"Error: {error_msg}"

        return {"status": "success"}

if __name__ == '__main__':
    generator: AnalyticsOutputGenerator = AnalyticsOutputGenerator()

    code_source: str = """
content = "Hello world!"

# File path
file_path = "abc.png"

# Write the string to the file
with open(file_path, "w", encoding="utf-8") as file:
    file.write(content)

    """

    target: str = f"s3://aaa-storage/abc-{uuid.uuid4()}.png"
    result = generator.invoke({"code": code_source, "target": target}, {})

    print(f"RESULT: {result}")
