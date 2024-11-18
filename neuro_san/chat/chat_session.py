
# Copyright (C) 2023-2024 Cognizant Digital Business, Evolutionary AI.
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

from neuro_san.utils.stream_to_logger import StreamToLogger


class ChatSession:
    """
    Interface for Chat whose clients are usually DirectSessions from gRPC services.
    Note that these are *not* Sessions in a gRPC service sense, but they do typically
    last between multiple calls to a service.
    """

    async def set_up(self):
        """
        Resets or sets the instance up for the first time.
        """
        raise NotImplementedError

    async def chat(self, user_input: str, sly_data: Dict[str, Any]):
        """
        Main entry-point method for accepting new user input

        :param user_input: A string with the user's input
        :param sly_data: A mapping whose keys might be referenceable by agents, but whose
                 values should not appear in agent chat text. Can be None.

        Note that nothing is returned immediately as processing
        the chat happens asynchronously and might take longer
        than the lifetime of a socket.  Results are polled from
        get_latest_response() below.
        """
        raise NotImplementedError

    def get_logger(self) -> StreamToLogger:
        """
        :return: The StreamToLogger which has been capturing all the "thinking" messages.
        """
        raise NotImplementedError

    def get_latest_response(self) -> str:
        """
        :return: The most recent response to the user from the chat agent.
                Can be None if the chat agent is still chewing on the previous user input.
        """
        raise NotImplementedError

    def clear_latest_response(self):
        """
        Clears out the latest response so as not to return duplicates.
        """
        raise NotImplementedError

    async def delete_resources(self):
        """
        Frees up any service-side resources.
        """
        raise NotImplementedError

    def get_last_input_timestamp(self) -> Any:
        """
        :return: The result of datetime.now() when the chat agent
                last received input.
        """
        raise NotImplementedError
