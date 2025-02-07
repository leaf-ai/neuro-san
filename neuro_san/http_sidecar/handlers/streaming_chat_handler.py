
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
from typing import Any, Dict, Type
import json
import grpc

from tornado.web import RequestHandler
from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import Parse

# pylint: disable=no-name-in-module
from neuro_san.api.grpc.agent_pb2 import ChatRequest, ChatResponse
from neuro_san.client.agent_session_factory import AgentSessionFactory


class StreamingChatHandler:
    """
    Factory class for constructing handler class for neuro-san
    streaming chat API call.
    """

    def build(self, port: int, agent_name: str, method_name: str) -> Type:
        """
        Factory method.
        :param port: port for gRPC service we will use;
        :param agent_name: name of agent this API method is implemented for;
        :param method_name: name of API method;
        :return: dynamically constructed Python type to be used by Tornado application
            for API method handling.
        """

        def post(self):
            """
            Implementation of POST request handler for streaming chat API call.
            """
            try:
                # Parse JSON body
                data = json.loads(self.request.body)
                print(f"Received POST request with data: {data}")

                grpc_request = Parse(json.dumps(data), ChatRequest())

                grpc_session = AgentSessionFactory().create_session("service", agent_name, port=port)
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
            except Exception as e:
                # Handle unexpected errors
                self.set_status(500)
                self.write({"error": "Internal server error"})
                self.flush()

            self.finish()

        # Dynamically construct Python type implementing RequestHandler
        # for this specific method.
        return type(f"{method_name}_handler", (RequestHandler,), {"post": post})

