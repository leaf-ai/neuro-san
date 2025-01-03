
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
from enum import Enum
from typing import Dict
from typing import Type

from langchain_core.messages.ai import AIMessage
from langchain_core.messages.base import BaseMessage
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.system import SystemMessage
from langchain_core.messages.tool import ToolMessage

from neuro_san.messages.agent_framework_message import AgentFrameworkMessage
from neuro_san.messages.agent_message import AgentMessage
from neuro_san.messages.legacy_logs_message import LegacyLogsMessage


class ChatMessageType(Enum):
    """
    Python enum to mimic gRPC for chat.ChatMessageType without dragging in all of gRPC.
    These all need to match what is defined in chat.proto
    """
    UNKNOWN_MESSAGE_TYPE = 0
    SYSTEM = 1
    HUMAN = 2
    TOOL = 3
    AI = 4

    AGENT = 100
    AGENT_FRAMEWORK = 101
    LEGACY_LOGS = 102


# Convenience mappings going between constants and class types
MESSAGE_TYPE_TO_CHAT_MESSAGE_TYPE: Dict[Type[BaseMessage], int] = {
    # Needs to match chat.proto
    SystemMessage: ChatMessageType.SYSTEM,
    HumanMessage: ChatMessageType.HUMAN,
    ToolMessage: ChatMessageType.TOOL,
    AIMessage: ChatMessageType.AI,

    AgentMessage: ChatMessageType.AGENT,
    AgentFrameworkMessage: ChatMessageType.AGENT_FRAMEWORK,
    LegacyLogsMessage: ChatMessageType.LEGACY_LOGS,
}


MESSAGE_TYPE_TO_ROLE: Dict[Type[BaseMessage], str] = {
    AIMessage: "assistant",
    HumanMessage: "user",
    ToolMessage: "tool",
    SystemMessage: "system",
    AgentMessage: "agent",
    AgentFrameworkMessage: "agent-framework",
    LegacyLogsMessage: "legacy-logs",
}
