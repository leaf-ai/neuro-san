
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
"""
See class comment for details
"""
from typing import Any, Dict
import json

from tornado.web import RequestHandler

from neuro_san.interfaces.agent_session import AgentSession
from neuro_san.client.agent_session_factory import AgentSessionFactory


class ConnectivityHandler(RequestHandler):
    """
    Handler class for neuro-san "connectivity" API call.
    """
    # pylint: disable=too-few-public-methods

    def initialize(self, request_data):
        # request_data is a dictionary with keys:
        # "agent_name": agent name as a string;
        # "port": integer value for gRPC service port.
        self.agent_name: str = request_data.get("agent_name", "unknown")
        self.port: int = request_data.get("port", AgentSession.DEFAULT_PORT)

    def get(self):
        """
        Implementation of GET request handler for "connectivity" API call.
        """

        try:
            data: Dict[str, Any] = {}
            factory: AgentSessionFactory = self.application.get_session_factory()
            grpc_session: AgentSession =\
                factory.create_session("service", self.agent_name, self.port)
            result_dict: Dict[str, Any] = grpc_session.connectivity(data)

            # Return gRPC response to the HTTP client
            self.set_header("Content-Type", "application/json")
            self.write(result_dict)

            # Log the response
            print(f"Sent response: {result_dict}")

        except json.JSONDecodeError:
            # Handle invalid JSON input
            self.set_status(400)
            self.write({"error": "Invalid JSON format"})
        except Exception as exc:  # pylint: disable=broad-exception-caught
            # Handle unexpected errors
            self.set_status(500)
            self.write({"error": f"Internal server error: {exc}"})
