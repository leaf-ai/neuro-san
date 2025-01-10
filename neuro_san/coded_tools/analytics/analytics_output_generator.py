import time
from typing import Any
from typing import Dict
from typing import List
from typing import Union

import uuid
import random

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
                    "code_snippet" A string containing well-formed Python code segment;
                    "project_name" A string with S3 full destination path for code execution result
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
        code_source: str = args.get("code_snippet", "")
        if not code_source:
            print("NO code string provided!")
            return "Error: NO CODE"
        project_name: str = args.get("project_name", "fedex_day")
        if not project_name:
            print("NO project_name provided!")
            return "Error: NO PROJECT NAME"

        service_endpoint: str = "localhost:30012"
        client = GRPCTaskClient(service_endpoint)

        task_id: str = f"task-{uuid.uuid4()}"
        dest_uri: str = self.generate_destination_uri(project_name)

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

    def generate_destination_uri(self, project_name: str, login: str = "fedex") -> str:
        """
        Function generates S3 URI for a dataset file created by data generation task;
        dataset will be uploaded to this URI.
        """
        bucket: str = "aaa-storage"
        project: str = self.make_s3_acceptable(project_name)
        generation_time: str = self.get_s3_acceptable_time()
        return f"s3://{bucket}/{login}/{project}_generated_{generation_time}.png"

    def generate_short_uuid(self, length=12) -> str:
        """
        Utility function to generate UUID string of given length.
        """
        # Generate a random UUID
        random_uuid = uuid.uuid4()
        # Convert the UUID to a string without dashes
        uuid_str = str(random_uuid).replace('-', '')
        # Return the first `length` characters of the UUID
        return uuid_str[:length]

    def make_s3_acceptable(self, name: str) -> str:
        """
        Utility function to convert some name into a string
        suitable to be a part of S3 URI.
        """
        # Replace spaces with hyphens or URL-encode them
        name = name.replace(" ", "-")
        # Lowercase the string (required for bucket names)
        name = name.lower()
        # URL encode the name to make it URI-safe
        s3_acceptable_name = quote(name, safe='-')
        return s3_acceptable_name

    def get_s3_acceptable_time(self) -> str:
        """
        Utility function to generate timestamp in a format
        suitable to be a part of S3 URI.
        """
        # Get the current time
        now = datetime.now()
        # Format the time in a human-readable string without spaces or colons
        readable_time = now.strftime("%Y-%m-%d-%H-%M")
        return readable_time


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
    result = generator.invoke({"code_snippet": code_source, "project_name": "test-01"}, {})

    print(f"RESULT: {result}")
