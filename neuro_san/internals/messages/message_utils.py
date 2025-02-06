
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

import json

from langchain_core.messages.ai import AIMessage
from langchain_core.messages.base import BaseMessage
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.system import SystemMessage
from langchain_core.messages.tool import ToolMessage

from neuro_san.internals.messages.chat_message_type import ChatMessageType


def pretty_the_messages(messages: List[Any]) -> str:
    """
    Pretty printing helper
    :param messages: A list of OpenAI messages
    :return: A single string representing the output of the messages.
    """
    prettied = ""
    messages_list = list(messages)  # Convert to list to allow reversing

    # Iterate in reverse to find the last user message
    rm = []
    for m in reversed(messages_list):
        rm.append(m)
        if get_role(m) == "user":
            break

    for m in reversed(rm):
        if any(get_content(m)):
            prettied += f"{get_role(m)}: {get_content(m)}\n"

    return prettied


def get_last_message_with_content(messages: List[Any]) -> object:
    """
    Sometimes just indexing a message list by [-1]
    gives you a message that does not actually have any content.
    This method gives you the last messages that does have content.

    :param messages: input list of OpenAI messages
    :return: An applicalble OpenAI message (or None if no message is applicable)
    """

    messages_list = list(messages)

    for m in reversed(messages_list):
        if any(get_content(m)):
            return m

    return None


def generate_response(the_messages: List[Any]) -> str:
    """
    :param the_messages: A list of OpenAI messages
    :return: a JSON-ification of the list of messages.
    """
    response_list = []
    for i, m in enumerate(the_messages):
        # Duplicate the assistant role message before every tool response role message
        if get_role(m) == "tool" and i > 0 and get_role(the_messages[i - 1]) == "assistant":
            assistant_message = {
                "role": get_role(the_messages[i - 1]),
                "content": get_content(the_messages[i - 1])
            }
            response_list.append(assistant_message)

        message_dict = {
            "role": get_role(m),
            "content": get_content(m)
        }
        response_list.append(message_dict)

    return json.dumps(response_list)


def get_role(message: Any) -> str:
    """
    :param message: Either an OpenAI message or a langchain BaseMessage
    :return: A string describing the role of the message
    """

    if hasattr(message, "role"):
        return message.role

    # Check the look-up table above
    role: str = ChatMessageType.message_to_role(message)
    if role is not None:
        return role

    raise ValueError(f"Don't know how to handle message type {message.__class__.__name__}")


def get_content(message: Any) -> str:
    """
    :param message: Either an OpenAI message or a langchain BaseMessage
    :return: A string describing the content of the message
    """

    if isinstance(message, BaseMessage):
        return message.content

    if hasattr(message, "content"):
        if not any(message.content):
            return ""
        return message.content[0].text.value

    raise ValueError(f"Don't know how to handle message type {message.__class__.__name__}")


def convert_to_chat_message(message: BaseMessage, origin: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convert the BaseMessage to a chat.ChatMessage dictionary

    :param message: The BaseMessage to convert
    :param origin: A List of origin dictionaries indicating the origin of the run.
            The origin can be considered a path to the original call to the front-man.
            Origin dictionaries themselves each have the following keys:
                "tool"                  The string name of the tool in the spec
                "instantiation_index"   An integer indicating which incarnation
                                        of the tool is being dealt with.
    :return: The ChatMessage in dictionary form
    """

    message_type: ChatMessageType = ChatMessageType.from_message(message)
    chat_message: Dict[str, Any] = {
        "type": message_type,
        # No mime_data for now
    }

    # Handle the origin information if we have it
    if origin is not None:
        chat_message["origin"] = origin

    # Dictionary of BaseMessage field sources to ChatMessage destinations
    # Anything in this dictionary is considered optional and we only populate
    # the field on ChatMessage if it has a value.
    optionals: Dict[str, str] = {
        "content": "text",
        "chat_context": "chat_context"
    }
    for src, dest in optionals.items():
        value: Any = getattr(message, src)
        if value is not None:
            chat_message[dest] = value

    return chat_message


def convert_to_base_message(chat_message: Dict[str, Any]) -> BaseMessage:
    """
    :param chat_message: A ChatMessage dictionary to convert into BaseMessage
    :return: A BaseMessage that was converted from the input.
            Can return None if conversion could not take place
    """
    base_message: BaseMessage = None
    if chat_message is None:
        return base_message

    content: str = chat_message.get("text")
    chat_message_type: ChatMessageType = ChatMessageType.from_response_type(chat_message.get("type"))

    if chat_message_type == ChatMessageType.SYSTEM:
        base_message = SystemMessage(content=content)
    elif chat_message_type == ChatMessageType.HUMAN:
        base_message = HumanMessage(content=content)
    elif chat_message_type == ChatMessageType.TOOL:
        base_message = ToolMessage(content=content)
    elif chat_message_type == ChatMessageType.AI:
        base_message = AIMessage(content=content)

    # Any other message type we do not want to send to agent as history.

    return base_message
