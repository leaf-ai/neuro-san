from typing import Any, Callable, Dict
import json
import grpc

from tornado.web import RequestHandler
from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import Parse


class HandlerFactory:

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        print(f"Endpoint: {endpoint}")

    def _build(self, method_name: str, method_class, endpoint: str) -> Callable:

        def post(self):
            try:
                # Parse JSON body
                data = json.loads(self.request.body)
                print(f"Received POST request with data: {data}")

                grpc_request = Parse(json.dumps(data), method_class())

                result_dict: Dict[str, Any] = {}
                with grpc.insecure_channel(endpoint) as channel:
                    client = InferenceServiceStub(channel)
                    print(f"gRPC client created. Connected to: {endpoint}")

                    # grpc_method = None
                    # try:
                    #     grpc_method = getattr(client, method_name)
                    # except AttributeError:
                    #     print(f"The service method {method_name} does not exist.")
                    #
                    # result = grpc_method(grpc_request)
                    # result_dict = MessageToDict(result)
                # inference_result = result_dict.get("response", None)
                # if inference_result is not None and isinstance(inference_result, str):
                #     result_dict["response"] = json.loads(inference_result)

                # Return gRPC response to the HTTP client
                self.set_header("Content-Type", "application/json")
                self.write({"message": result_dict})

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

        return type(f"{method_name}_handler", (RequestHandler,), {"post": post})

    def build(self, method_name: str, method_class) -> Callable:
        return self._build(method_name, method_class, self.endpoint)
