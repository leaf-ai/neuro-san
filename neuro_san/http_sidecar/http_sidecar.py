
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

import copy
from typing import Any, Dict, List

from tornado.ioloop import IOLoop
from tornado.web import Application

from neuro_san.http_sidecar.logging.http_logger import HttpLogger
from neuro_san.service.agent_server import DEFAULT_FORWARDED_REQUEST_METADATA

from neuro_san.http_sidecar.interfaces.agent_authorizer import AgentAuthorizer
from neuro_san.http_sidecar.handlers.health_check_handler import HealthCheckHandler
from neuro_san.http_sidecar.handlers.connectivity_handler import ConnectivityHandler
from neuro_san.http_sidecar.handlers.function_handler import FunctionHandler
from neuro_san.http_sidecar.handlers.streaming_chat_handler import StreamingChatHandler
from neuro_san.http_sidecar.handlers.concierge_handler import ConciergeHandler
from neuro_san.http_sidecar.handlers.openapi_publish_handler import OpenApiPublishHandler


class HttpSidecar(AgentAuthorizer):
    """
    Class provides simple http endpoint for neuro-san API,
    working as a client to neuro-san gRPC service.
    """
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    # pylint: disable=too-many-instance-attributes
    def __init__(self, port: int, http_port: int,
                 agents: Dict[str, Any],
                 openapi_service_spec_path: str,
                 forwarded_request_metadata: str = DEFAULT_FORWARDED_REQUEST_METADATA):
        """
        Constructor:
        :param port: port for gRPC neuro-san service;
        :param http_port: port for http neuro-san service;
        :param agents: dictionary of registered agents;
        :param openapi_service_spec_path: path to a file with OpenAPI service specification;
        :param forwarded_request_metadata: A space-delimited list of http metadata request keys
               to forward to logs/other requests
        """
        self.server_name_for_logs: str = "Http Server"
        self.port = port
        self.http_port = http_port
        self.agents = copy.deepcopy(agents)
        self.logger = None
        self.openapi_service_spec_path: str = openapi_service_spec_path
        self.forwarded_request_metadata: List[str] = forwarded_request_metadata.split(" ")
        self.allowed_agents: Dict[str, bool] = {}

    def __call__(self):
        """
        Method to be called by a process running tornado HTTP server
        to actually start serving requests.
        """
        self.logger = HttpLogger(self.forwarded_request_metadata)

        app = self.make_app()
        app.listen(self.http_port)
        self.logger.info({}, "HTTP server is running on port %d", self.http_port)
        self.logger.debug({}, "Serving agents: %s", repr(self.agents.keys()))
        # Put agent names into "allowed" list:
        self.allowed_agents = {}
        for agent_name, _ in self.agents.items():
            self.allowed_agents[agent_name] = True
        IOLoop.current().start()

    def make_app(self):
        """
        Construct tornado HTTP "application" to run.
        """
        request_data: Dict[str, Any] = self.build_request_data()
        handlers = []
        handlers.append(("/", HealthCheckHandler))
        handlers.append(("/api/v1/list", ConciergeHandler, request_data))
        handlers.append(("/api/v1/docs", OpenApiPublishHandler, request_data))

        # Register templated request paths for agent API methods:
        # regexp format used here is that of Python Re standard library.
        handlers.append((r"/api/v1/([^/]+)/function", FunctionHandler, request_data))
        handlers.append((r"/api/v1/([^/]+)/connectivity", ConnectivityHandler, request_data))
        handlers.append((r"/api/v1/([^/]+)/streaming_chat", StreamingChatHandler, request_data))

        return Application(handlers)

    def allow(self, agent_name) -> bool:
        return self.allowed_agents.get(agent_name, False)

    def build_request_data(self) -> Dict[str, Any]:
        """
        Build request data for Http handlers.
        :return: a dictionary with request data to be passed to a http handler.
        """
        return {
            "agent_policy": self,
            "port": self.port,
            "forwarded_request_metadata": self.forwarded_request_metadata,
            "openapi_service_spec_path": self.openapi_service_spec_path
        }
