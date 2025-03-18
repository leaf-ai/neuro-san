
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

from neuro_san.interfaces.agent_session import AgentSession


class ConciergeSession:
    """
    Interface for a Concierge session.
    """

    # Default port for the Concierge Service
    # This port number will also be mentioned in its Dockerfile
    DEFAULT_PORT: int = AgentSession.DEFAULT_PORT

    # Default port for the Concierge HTTP Service
    # This port number will also be mentioned in its Dockerfile
    DEFAULT_HTTP_PORT: int = AgentSession.DEFAULT_HTTP_PORT

    def list(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the ConciergeRequest
                    protobuf structure. Has the following keys:
                        <None>
        :return: A dictionary version of the ConciergeResponse
                    protobuf structure. Has the following keys:
                "agents" - the sequence of dictionaries describing available agents
        """
        raise NotImplementedError
