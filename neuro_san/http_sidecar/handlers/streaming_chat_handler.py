
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
from typing import Any, Dict, Generator
import json
import traceback

from google.protobuf.json_format import MessageToDict
from google.protobuf.json_format import Parse

# pylint: disable=no-name-in-module
from neuro_san.api.grpc.agent_pb2 import ChatRequest

from neuro_san.http_sidecar.handlers.base_request_handler import BaseRequestHandler


class StreamingChatHandler(BaseRequestHandler):
    """
    Handler class for neuro-san streaming chat API call.
    """

    def post(self):
        """
        Implementation of POST request handler for streaming chat API call.
        """
        try:
            # Parse JSON body
            data = json.loads(self.request.body)

            grpc_request = Parse(json.dumps(data), ChatRequest())

            result_generator: Generator[Dict[str, Any], None, None] =\
                self.grpc_session.streaming_chat(grpc_request)

            # Set up headers for chunked response
            self.set_header("Content-Type", "application/json")
            self.set_header("Transfer-Encoding", "chunked")
            # Flush headers immediately
            self.flush()

            for result_message in result_generator:
                result_dict: Dict[str, Any] = MessageToDict(result_message)
                result_str: str = json.dumps(result_dict) + "\n"
                self.write(result_str)
                self.flush()

        except json.JSONDecodeError:
            # Handle invalid JSON input
            self.set_status(400)
            self.write({"error": "Invalid JSON format"})
        except Exception:  # pylint: disable=broad-exception-caught
            # Handle unexpected errors
            self.set_status(500)
            self.write({"error": "Internal server error"})
            self.logger.error("Internal server error: %s", traceback.format_exc())
        finally:
            self.flush()
        # We are done with response stream:
        self.finish()
