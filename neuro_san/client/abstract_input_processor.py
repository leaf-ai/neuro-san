
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
from typing import Dict

from neuro_san.internals.messages.chat_message_type import ChatMessageType


# pylint: disable=too-many-instance-attributes
class AbstractInputProcessor:
    """
    Abstract class for Processing AgentCli input.
    Use one of the concrete classes directly instead of this one.
    """

    def __init__(self):
        """
        Constructor
        """
        self.session_id: str = None

    def process_once(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Employ the subclass's strategy to communicate with agent.
        :param state: The state dictionary to pass around
        :return: An updated state dictionary
        """
        raise NotImplementedError

    def formulate_chat_request(self, user_input: str, sly_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Formulates a single chat request given the user_input
        :param user_input: The string to send
        :param sly_data: The sly_data dictionary to send
        :return: A dictionary representing the chat request to send
        """
        chat_request = {
            "session_id": self.session_id,
            "user_message": {
                "type": ChatMessageType.HUMAN,
                "text": user_input
            }
        }

        if sly_data is not None and len(sly_data.keys()) > 0:
            chat_request["sly_data"] = sly_data

        return chat_request
