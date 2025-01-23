from typing import Any, Dict
import json
import grpc

from tornado.web import RequestHandler
from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import Parse

from neuro_san.client.agent_session_factory import AgentSessionFactory

# pylint: disable=no-name-in-module
from neuro_san.api.grpc.agent_pb2 import FunctionRequest, FunctionResponse


class FunctionHandler:

    def build(self, port: int, agent_name: str, method_name: str):
        def get(self):
            try:
                # Parse JSON body
                # data = json.loads(self.request.body)
                # print(f"Received POST request with data: {data}")

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
                print("Invalid JSON received")
                self.set_status(400)
                self.write({"error": "Invalid JSON format"})
            except Exception as e:
                # Handle unexpected errors
                print(f"Error processing request: {e}")
                self.set_status(500)
                self.write({"error": "Internal server error"})

        return type(f"{method_name}_handler", (RequestHandler,), {"get": get})



