
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
from collections.abc import Sequence
from typing import Any
from typing import Dict

from pydantic import ConfigDict

from langchain_core.agents import AgentAction
from langchain_core.agents import AgentFinish
from langchain_core.callbacks.base import AsyncCallbackHandler
from langchain_core.documents import Document
from langchain_core.outputs import LLMResult
from langchain_core.outputs.chat_generation import ChatGeneration

from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.agent_message import AgentMessage


# pylint: disable=too-many-ancestors
class JournalingCallbackHandler(AsyncCallbackHandler):
    """
    AsyncCallbackHandler implementation that intercepts agent-level chatter
    """

    # Declarations of member variables here satisfy Pydantic style,
    # which is a type validator that langchain is based on which
    # is able to use JSON schema definitions to validate fields.
    journal: Journal

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, journal: Journal):
        """
        Constructor

        :param journal: The journal to write messages to
        """
        self.journal: Journal = journal

    async def on_llm_end(self, response: LLMResult,
                         **kwargs: Any) -> None:
        # print(f"In on_llm_end() with {response}")
        generations = response.generations[0]
        first_generation = generations[0]
        if isinstance(first_generation, ChatGeneration):
            # DEF There can be token counts in the usage_metadata field as well
            content: str = first_generation.text
            if content is not None and len(content) > 0:
                message = AgentMessage(content=content)
                await self.journal.write_message(message)

    async def on_chain_end(self, outputs: Dict[str, Any],
                           **kwargs: Any) -> None:
        # print(f"In on_chain_end() with {outputs}")
        return

    async def on_tool_end(self, output: Any,
                          **kwargs: Any) -> None:
        # print(f"In on_tool_end() with {output}")
        return

    async def on_agent_action(self, action: AgentAction,
                              **kwargs: Any) -> None:
        # print(f"In on_agent_action() with {action}")
        return

    async def on_agent_finish(self, finish: AgentFinish,
                              **kwargs: Any) -> None:
        # print(f"In on_agent_finish() with {finish}")
        return

    async def on_retriever_end(self, documents: Sequence[Document],
                               **kwargs: Any) -> None:
        # print(f"In on_retriever_end() with {documents}")
        return
