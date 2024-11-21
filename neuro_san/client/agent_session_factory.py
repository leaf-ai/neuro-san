
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

from neuro_san.client.direct_agent_session_factory import DirectAgentSessionFactory
from neuro_san.session.agent_session import AgentSession
from neuro_san.session.service_agent_session import ServiceAgentSession


# pylint: disable=too-few-public-methods
class AgentSessionFactory:
    """
    Factory class for agent sessions.
    """

    @staticmethod
    def create_session(session_type: str,
                       agent_name: str,
                       hostname: str = None,
                       port: int = None) -> AgentSession:
        """
        :param session_type: The type of session to create
        :param agent_name: The name of the agent to use for the session.
        :param hostname: The name of the host to connect to (if applicable)
        :param port: The port on the host to connect to (if applicable)
        """
        session: AgentSession = None

        if session_type == "direct":
            factory = DirectAgentSessionFactory()
            session = factory.create_session(agent_name)
        elif session_type == "service":
            session = ServiceAgentSession(host=hostname, port=port, agent_name=agent_name)
        else:
            raise ValueError(f"session_type {session_type} is not understood")

        return session
