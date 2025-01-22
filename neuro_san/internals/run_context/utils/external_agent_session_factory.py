
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
from typing import Dict

import logging

# The only reach-around from internals outward.
from neuro_san.session.agent_session import AgentSession
from neuro_san.session.async_service_agent_session import AsyncServiceAgentSession


# pylint: disable=too-few-public-methods
class ExternalAgentSessionFactory:
    """
    Creates AgentSessions for external agents.
    """

    @staticmethod
    def create_session(agent_location: Dict[str, str]) -> AgentSession:
        """
        :param agent_location: An agent location dictionary returned by
                    ExternalAgentParsing.parse_external_agent()
        :return: An AgentSession through which communications about the external agent can be made.
        """
        if agent_location is None:
            return None

        # Create the session.
        host = agent_location.get("host")
        port = agent_location.get("port")
        agent_name = agent_location.get("agent_name")
        service_prefix = agent_location.get("service_prefix")

        # Optimization:
        #   It's possible we might want to create a different kind of session
        #   to minimize socket usage, but for now use the AsyncServiceAgentSession
        #   so as to ensure proper logging even on the same server (localhost).
        session = AsyncServiceAgentSession(host, port, agent_name=agent_name,
                                           service_prefix=service_prefix)

        # Quiet any logging from leaf-common grpc stuff.
        quiet_please = logging.getLogger("leaf_common.session.grpc_client_retry")
        quiet_please.setLevel(logging.WARNING)

        return session
