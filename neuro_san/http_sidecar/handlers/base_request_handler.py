
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
import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import grpc
from tornado.web import RequestHandler

from neuro_san.interfaces.async_agent_session import AsyncAgentSession
from neuro_san.interfaces.concierge_session import ConciergeSession
from neuro_san.session.async_grpc_service_agent_session import AsyncGrpcServiceAgentSession
from neuro_san.session.grpc_concierge_session import GrpcConciergeSession


class BaseRequestHandler(RequestHandler):
    """
    Abstract handler class for neuro-san API calls.
    Provides logic to inject neuro-san service specific data
    into local handler context.
    """
    grpc_to_http = {
        grpc.StatusCode.INVALID_ARGUMENT: 400,
        grpc.StatusCode.UNAUTHENTICATED: 401,
        grpc.StatusCode.PERMISSION_DENIED: 403,
        grpc.StatusCode.NOT_FOUND: 404,
        grpc.StatusCode.ALREADY_EXISTS: 409,
        grpc.StatusCode.INTERNAL: 500,
        grpc.StatusCode.UNAVAILABLE: 503,
        grpc.StatusCode.DEADLINE_EXCEEDED: 504
    }

    request_id: int = 0

    # pylint: disable=attribute-defined-outside-init
    def initialize(self, agent_name, port, forwarded_request_metadata):
        """
        This method is called by Tornado framework to allow
        injecting service-specific data into local handler context.
        :param agent_name: name of receiving neuro-san agent
        :param port: gRPC service port.
        :param forwarded_request_metadata: request metadata to forward.
        """
        #
        self.agent_name: str = agent_name
        self.port: int = port
        self.forwarded_request_metadata: List[str] = forwarded_request_metadata
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_metadata(self) -> Dict[str, Any]:
        """
        Extract user metadata defined by self.forwarded_request_metadata list
        from incoming request.
        :return: dictionary of user request metadata; possibly empty
        """
        headers: Dict[str, Any] = self.request.headers
        result: Dict[str, Any] = {}
        for item_name in self.forwarded_request_metadata:
            if item_name in headers.keys():
                result[item_name] = headers[item_name]
        return result

    def get_request_id(self, metadata: Dict[str, str]) -> str:
        """
        Get unique request id for logging purposes.
        :param metadata: incoming request metadata
        """
        # If request metadata has "request_id" already specified, use it:
        req_id: str = metadata.get("request_id", None)
        if req_id:
            return req_id
        req_id = f"request-{BaseRequestHandler.request_id}"
        BaseRequestHandler.request_id += 1
        return req_id

    def get_agent_grpc_session(self, metadata: Dict[str, Any]) -> AsyncAgentSession:
        """
        Build gRPC session to talk to "main" service
        :return: AgentSession to use
        """
        grpc_session: AsyncAgentSession = \
            AsyncGrpcServiceAgentSession(
                host="localhost",
                port=self.port,
                metadata=metadata,
                agent_name=self.agent_name)
        return grpc_session

    def get_concierge_grpc_session(self, metadata: Dict[str, Any]) -> ConciergeSession:
        """
        Build gRPC session to talk to "concierge" service
        :return: ConciergeSession to use
        """
        grpc_session: ConciergeSession = \
            GrpcConciergeSession(
                host="localhost",
                port=self.port,
                metadata=metadata)
        return grpc_session

    def extract_grpc_error_info(self, exc: grpc.aio.AioRpcError) -> Tuple[int, str, str]:
        """
        Extract user-friendly information from gRPC exception
        :param exc: gRPC service exception
        :return: tuple of 3 values:
            corresponding HTTP error code;
            name of gRPC code;
            string with additional error details.
        """
        code = exc.code()
        http_code = BaseRequestHandler.grpc_to_http.get(code, 500)
        return http_code, code.name, exc.details()

    def process_exception(self, exc: Exception):
        """
        Process exception raised during request handling
        """
        if exc is None:
            return
        if isinstance(exc, json.JSONDecodeError):
            # Handle invalid JSON input
            self.set_status(400)
            self.write({"error": "Invalid JSON format"})
            self.logger.error("error: Invalid JSON format")
            return

        if isinstance(exc, grpc.aio.AioRpcError):
            http_status, err_name, err_details =\
                self.extract_grpc_error_info(exc)
            self.set_status(http_status)
            err_msg: str = f"status: {http_status} grpc: {err_name} details: {err_details}"
            self.write({"error": err_msg})
            self.logger.error("Http server error: %s", err_msg)
            return

        # General exception case:
        self.set_status(500)
        self.write({"error": "Internal server error"})
        self.logger.error("Internal server error: %s", str(exc))

    def data_received(self, chunk):
        """
        Method overrides abstract method of RequestHandler
        with no-op implementation.
        """
        return
