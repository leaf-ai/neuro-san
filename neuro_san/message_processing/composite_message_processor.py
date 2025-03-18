
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
from typing import List

from neuro_san.internals.filters.message_filter import MessageFilter
from neuro_san.internals.messages.chat_message_type import ChatMessageType
from neuro_san.message_processing.message_processor import MessageProcessor


class CompositeMessageProcessor(MessageProcessor):
    """
    A MessageProcessor implementation that employs multiple MessageProcessors.
    """

    def __init__(self, message_processors: List[MessageProcessor] = None,
                 depth_blocks_breadth: bool = False):
        """
        Constructor

        :param message_processors: An ordered List of MessageProcessors with which
                     this instance will process messages
        :param depth_blocks_breadth: When True, any one component of this instance (depth)
                    can block further message processing of downstream peers (breadth).
        """
        self.message_processors: List[MessageProcessor] = message_processors
        if self.message_processors is None:
            self.message_processors = []
        self.depth_blocks_breadth: bool = depth_blocks_breadth

    def add_processor(self, message_processor: MessageProcessor):
        """
        Adds a MessageProcessor to the list.
        Order can be important.

        :param message_processor: The MessageProcessor to add
        """
        if message_processor is not None:
            self.message_processors.append(message_processor)

    def reset(self):
        """
        Resets any previously accumulated state
        """
        for message_processor in self.message_processors:
            message_processor.reset()

    def should_block_downstream_processing(self, chat_message_dict: Dict[str, Any],
                                           message_type: ChatMessageType) -> bool:
        """
        :param chat_message_dict: The ChatMessage dictionary to consider.
        :param message_type: The ChatMessageType of the chat_message_dictionary to process.
        :return: True if the given message should be blocked from further downstream
                processing.  False otherwise (the default).
        """
        if not self.depth_blocks_breadth:
            return False

        for message_processor in self.message_processors:
            if message_processor.should_block_downstream_processing(chat_message_dict, message_type):
                return True
        return False

    def process_message(self, chat_message_dict: Dict[str, Any], message_type: ChatMessageType = None):
        """
        Process the message.
        :param chat_message_dict: The ChatMessage dictionary to process.
        :param message_type: The ChatMessageType of the chat_message_dictionary to process.
                            Can be None to kick the process off.
        """
        if message_type is None:
            message_type = MessageFilter.get_message_type(chat_message_dict)

        for message_processor in self.message_processors:
            message_processor.process_message(chat_message_dict, message_type)
            if message_processor.should_block_downstream_processing(chat_message_dict, message_type):
                break

    async def async_process_message(self, chat_message_dict: Dict[str, Any], message_type: ChatMessageType = None):
        """
        Process the message asynchronously.

        :param chat_message_dict: The ChatMessage dictionary to process.
        :param message_type: The ChatMessageType of the chat_message_dictionary to process.
                            Can be None to kick the process off.
        """
        if message_type is None:
            message_type = MessageFilter.get_message_type(chat_message_dict)

        for message_processor in self.message_processors:
            await message_processor.async_process_message(chat_message_dict, message_type)
            if message_processor.should_block_downstream_processing(chat_message_dict, message_type):
                break
