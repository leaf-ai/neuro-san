
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
from tornado.web import RequestHandler

from neuro_san.interfaces.agent_session import AgentSession
from neuro_san.client.agent_session_factory import AgentSessionFactory


class BaseRequestHandler(RequestHandler):
    """
    Abstract handler class for neuro-san API calls.
    Provides logic to inject neuro-san service specific data
    into local handler context.
    """
    # pylint: disable=attribute-defined-outside-init
    def initialize(self, agent_name, port):
        """
        This method is called by Tornado framework to allow
        injecting service-specific data into local handler context.
        :param agent_name: name of receiving neuro-san agent
        :param port: gRPC service port.
        """
        #
        self.agent_name: str = agent_name
        self.port: int = port
        factory: AgentSessionFactory = self.application.get_session_factory()
        self.grpc_session: AgentSession = \
            factory.create_session("grpc", self.agent_name, hostname="localhost", port=self.port)
        self.logger = logging.getLogger(self.__class__.__name__)

    def data_received(self, chunk):
        """
        Method overrides abstract method of RequestHandler
        with no-op implementation.
        """
        return
