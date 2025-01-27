
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

from neuro_san.session.agent_session import AgentSession


# pylint: disable=too-few-public-methods
class AsyncAgentSessionFactory:
    """
    Creates asynchronous AgentSessions for external agents.
    """

    def create_session(self, agent_url: str, invocation_context: Any) -> AgentSession:
        """
        :param agent_url: A url string pointing to an external agent that came from
                    a tools list in an agent spec.
        :param invocation_context: The context policy container that pertains to the invocation
                    of the agent.

                    Note: At this interface level we are typing this as Any to avoid
                    an import cycle.  This will always be an InvocationContext.

        :return: An asynchronous implementation of AgentSession through which
                 communications about external agents can be made.
        """
        raise NotImplementedError
