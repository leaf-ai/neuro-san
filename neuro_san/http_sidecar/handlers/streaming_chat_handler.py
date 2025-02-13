
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
from typing import Any, Dict, Generator, Type
import json

from tornado.web import RequestHandler
from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import Parse

# pylint: disable=no-name-in-module
from neuro_san.api.grpc.agent_pb2 import ChatRequest
from neuro_san.client.agent_session_factory import AgentSessionFactory
from neuro_san.interfaces.agent_session import AgentSession


class StreamingChatHandler(RequestHandler):
    """
    Handler class for neuro-san streaming chat API call.
    """

    def initialize(self, request_data):
        # request_data is a dictionary with keys:
        # "agent_name": agent name as a string;
        # "port": integer value for gRPC service port.
        self.agent_name: str = request_data.get("agent_name", "unknown")
        self.port: int = request_data.get("port", AgentSession.DEFAULT_PORT)

    def post(self):
        """
        Implementation of POST request handler for streaming chat API call.
        """
        try:
            # Parse JSON body
            data = json.loads(self.request.body)
            print(f"Received POST request with data: {data}")

            grpc_request = Parse(json.dumps(data), ChatRequest())

            factory: AgentSessionFactory = self.application.get_session_factory()
            grpc_session: AgentSession =\
                factory.create_session("service", self.agent_name, self.port)
            result_generator: Generator[Dict[str, Any], None, None] =\
                grpc_session.streaming_chat(grpc_request)

            # Set up headers for chunked response
            self.set_header("Content-Type", "application/json")
            self.set_header("Transfer-Encoding", "chunked")
            # Flush headers immediately
            self.flush()

            for result_message in result_generator:
                result_dict: Dict[str, Any] = MessageToDict(result_message)
                result_str: str = json.dumps(result_dict) + "\n"
                print(f"CHAT HANDLER: |{result_dict}|\n\n")
                self.write(result_str)
                self.flush()

        except json.JSONDecodeError:
            # Handle invalid JSON input
            self.set_status(400)
            self.write({"error": "Invalid JSON format"})
            self.flush()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            # Handle unexpected errors
            self.set_status(500)
            self.write({"error": f"Internal server error: {exc}"})
            self.flush()

        self.finish()
