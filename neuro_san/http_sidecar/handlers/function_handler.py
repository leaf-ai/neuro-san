
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

from neuro_san.client.agent_session_factory import AgentSessionFactory


class FunctionHandler:
    """
    Factory class for constructing handler class for neuro-san
    "function" API call.
    """
    # pylint: disable=too-few-public-methods

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
            Implementation of GET request handler for "function" API call.
            """

            try:
                data: Dict[str, Any] = {}
                grpc_session = AgentSessionFactory().create_session("service", agent_name, port=port)
                result_dict: Dict[str, Any] = grpc_session.function(data)

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

        # Dynamically construct Python type implementing RequestHandler
        # for this specific method.
        return type(f"{method_name}_handler", (RequestHandler,), {"get": get})
