
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
from typing import List
from typing import TypeVar

from pydantic import ConfigDict

from langchain.agents.output_parsers.tools import ToolsAgentOutputParser
from langchain_core.outputs import Generation

from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.messages.agent_message import AgentMessage

T = TypeVar("T")


class JournalingToolsAgentOutputParser(ToolsAgentOutputParser):
    """
    ToolsAgentOutputParser implementation that intercepts agent-level chatter
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
        super().__init__(journal=journal)

    async def aparse_result(self, result: list[Generation], *, partial: bool = False) -> T:
        """Async parse a list of candidate model Generations into a specific format.

        The return value is parsed from only the first Generation in the result, which
            is assumed to be the highest-likelihood Generation.

        Args:
            result: A list of Generations to be parsed. The Generations are assumed
                to be different candidate outputs for a single model input.
            partial: Whether to parse the output as a partial result. This is useful
                for parsers that can parse partial results. Default is False.

        Returns:
            Structured output.
        """
        result = await super().aparse_result(result, partial=partial)
        if isinstance(result, List):
            for action in result:
                message = AgentMessage(content=action.log)
                await self.journal.write_message(message)
        # Note: We do not care about AgentFinish
        return result
