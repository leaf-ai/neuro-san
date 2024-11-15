from typing import List
from typing import Union

import json


class StreamToLogger:
    """
    Class for capturing output stream to a list of strings
    """

    VERBOSE: bool = False

    def __init__(self):
        """
        Constructor
        """
        self.log_content = []

    def write(self, message: Union[str, bytes]):
        """
        :param message: Add a message to the logs.
                    Can be either a string or bytes.
        """
        # Decoding bytes to string if necessary
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        self.log_content.append(message)

    def show_json(self, obj: object):
        """
        Add JSON from an object to the logs if VERBOSE is on.
        :param obj: Unclear what the typing expectation is here.
        """
        if self.VERBOSE:
            self.write(json.loads(obj.model_dump_json()))

    def get_logs(self) -> List[str]:
        """
        :return: A list of strings corresponding to log entries written
                with write() or show_json().
        """
        return self.log_content
