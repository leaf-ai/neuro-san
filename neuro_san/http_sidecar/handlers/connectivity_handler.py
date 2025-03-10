
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
import traceback

from neuro_san.http_sidecar.handlers.base_request_handler import BaseRequestHandler
from neuro_san.interfaces.async_agent_session import AsyncAgentSession


class ConnectivityHandler(BaseRequestHandler):
    """
    Handler class for neuro-san "connectivity" API call.
    """

    async def get(self):
        """
        Implementation of GET request handler for "connectivity" API call.
        """

        try:
            data: Dict[str, Any] = {}
            metadata: Dict[str, Any] = self.get_metadata()
            grpc_session: AsyncAgentSession = self.get_grpc_session(metadata)
            result_dict: Dict[str, Any] = await grpc_session.connectivity(data)

            # Return gRPC response to the HTTP client
            self.set_header("Content-Type", "application/json")
            self.write(result_dict)

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
