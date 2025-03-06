
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
import logging
from typing import Any
from typing import Dict
from typing import List
from tornado.web import RequestHandler

from neuro_san.interfaces.async_agent_session import AsyncAgentSession
from neuro_san.session.async_grpc_service_agent_session import AsyncGrpcServiceAgentSession


class BaseRequestHandler(RequestHandler):
    """
    Abstract handler class for neuro-san API calls.
    Provides logic to inject neuro-san service specific data
    into local handler context.
    """
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

    def get_grpc_session(self, metadata: Dict[str, Any]) -> AsyncAgentSession:
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

    def data_received(self, chunk):
        """
        Method overrides abstract method of RequestHandler
        with no-op implementation.
        """
        return
