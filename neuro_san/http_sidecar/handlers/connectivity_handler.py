
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
import grpc

from tornado.web import RequestHandler
from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import Parse

from neuro_san.client.agent_session_factory import AgentSessionFactory

# pylint: disable=no-name-in-module
from neuro_san.api.grpc.agent_pb2 import ConnectivityRequest, ConnectivityResponse


class ConnectivityHandler:
    """
    Factory class for constructing handler class for neuro-san
    "connectivity" API call.
    """

    def build(self, port: int, agent_name: str, method_name: str):
        """
        Factory method.
        :param port: port for gRPC service we will use;
        :param agent_name: name of agent this API method is implemented for;
        :param method_name: name of API method;
        :return: dynamically constructed Python type to be used by Tornado application
            for API method handling.
        """

        def get(self):
            """
            Implementation of GET request handler for "connectivity" API call.
            """

            try:
                data: Dict[str, Any] = {}
                grpc_session = AgentSessionFactory().create_session("service", agent_name, port=port)
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
            except Exception as e:
                # Handle unexpected errors
                self.set_status(500)
                self.write({"error": "Internal server error"})

        # Dynamically construct Python type implementing RequestHandler
        # for this specific method.
        return type(f"{method_name}_handler", (RequestHandler,), {"get": get})
