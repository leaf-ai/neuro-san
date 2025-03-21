
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

        metadata: Dict[str, Any] = self.get_metadata()
        request_id: int = self.get_request_id(metadata)
        self.logger.info("Start GET %s/function request [%s]", self.agent_name, request_id)
        try:
            data: Dict[str, Any] = {}
            grpc_session: AsyncAgentSession = self.get_agent_grpc_session(metadata)
            result_dict: Dict[str, Any] = await grpc_session.function(data)

            # Return gRPC response to the HTTP client
            self.set_header("Content-Type", "application/json")
            self.write(result_dict)

        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.process_exception(exc)
        finally:
            await self.flush()
            self.logger.info("Finish GET %s/function request [%s]", self.agent_name, request_id)
