
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


class FunctionHandler(BaseRequestHandler):
    """
    Handler class for neuro-san "function" API call.
    """

    async def get(self):
        """
        Implementation of GET request handler for "function" API call.
        """

        try:
            data: Dict[str, Any] = {}
            metadata: Dict[str, Any] = self.get_metadata()
            grpc_session: AsyncAgentSession = self.get_grpc_session(metadata)
            result_dict: Dict[str, Any] = await grpc_session.function(data)

            # Return gRPC response to the HTTP client
            self.set_header("Content-Type", "application/json")
            self.write(result_dict)

        except json.JSONDecodeError:
            # Handle invalid JSON input
            self.set_status(400)
            self.write({"error": "Invalid JSON format"})
        except grpc.aio.AioRpcError as exc:
            http_status, err_name, err_details =\
                self.extract_grpc_error_info(exc)
            self.set_status(http_status)
            err_msg: str = f"status: {http_status} grpc: {err_name} details: {err_details}"
            self.write({"error": err_msg})
            self.logger.error("Http server error: %s", err_msg)
        except Exception:  # pylint: disable=broad-exception-caught
            # Handle unexpected errors
            self.set_status(500)
            self.write({"error": "Internal server error"})
            self.logger.error("Internal server error: %s", traceback.format_exc())
        finally:
            await self.flush()
