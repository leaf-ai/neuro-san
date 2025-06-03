
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

import threading
from typing import Any, Dict, List

from tornado.ioloop import IOLoop

from neuro_san.interfaces.concierge_session import ConciergeSession
from neuro_san.session.direct_concierge_session import DirectConciergeSession
from neuro_san.service.agent_server import DEFAULT_FORWARDED_REQUEST_METADATA
from neuro_san.http_sidecar.logging.http_logger import HttpLogger
from neuro_san.http_sidecar.http_server_app import HttpServerApp

from neuro_san.http_sidecar.interfaces.agent_authorizer import AgentAuthorizer
from neuro_san.http_sidecar.interfaces.agents_updater import AgentsUpdater
from neuro_san.http_sidecar.handlers.health_check_handler import HealthCheckHandler
from neuro_san.http_sidecar.handlers.connectivity_handler import ConnectivityHandler
from neuro_san.http_sidecar.handlers.function_handler import FunctionHandler
from neuro_san.http_sidecar.handlers.streaming_chat_handler import StreamingChatHandler
from neuro_san.http_sidecar.handlers.concierge_handler import ConciergeHandler
from neuro_san.http_sidecar.handlers.openapi_publish_handler import OpenApiPublishHandler


class HttpSidecar(AgentAuthorizer, AgentsUpdater):
    """
    Class provides simple http endpoint for neuro-san API,
    working as a client to neuro-san gRPC service.
    """
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments, too-many-positional-arguments

    TIMEOUT_TO_START_SECONDS: int = 10

    def __init__(self, start_event: threading.Event,
                 port: int, http_port: int,
                 openapi_service_spec_path: str,
                 forwarded_request_metadata: str = DEFAULT_FORWARDED_REQUEST_METADATA):
        """
        Constructor:
        :param start_event: event to await before starting actual service;
        :param port: port for gRPC neuro-san service;
        :param http_port: port for http neuro-san service;
        :param openapi_service_spec_path: path to a file with OpenAPI service specification;
        :param forwarded_request_metadata: A space-delimited list of http metadata request keys
               to forward to logs/other requests
        """
        self.server_name_for_logs: str = "Http Server"
        self.start_event: threading.Event = start_event
        self.port = port
        self.http_port = http_port
        self.logger = None
        self.openapi_service_spec_path: str = openapi_service_spec_path
        self.forwarded_request_metadata: List[str] = forwarded_request_metadata.split(" ")
        self.allowed_agents: Dict[str, bool] = {}
        self.lock = None

    def __call__(self):
        """
        Method to be called by a thread running tornado HTTP server
        to actually start serving requests.
        """
        self.lock = threading.Lock()
        self.logger = HttpLogger(self.forwarded_request_metadata)
        app = self.make_app()

        # Wait for "go" signal which will be set by gRPC server and corresponding machinery
        # when everything is ready for servicing.
        event_set = self.start_event.wait(timeout=self.TIMEOUT_TO_START_SECONDS)
        if not event_set:
            self.logger.error({}, "Timeout (%d sec) waiting for HTTP server to start", self.TIMEOUT_TO_START_SECONDS)
            return

        app.listen(self.http_port)
        self.logger.info({}, "HTTP server is running on port %d", self.http_port)
        # Construct initial "allowed" list of agents:
        # no metadata to use here yet.
        self.update_agents(metadata={})
        self.logger.debug({}, "Serving agents: %s", repr(self.allowed_agents.keys()))

        IOLoop.current().start()

    def make_app(self):
        """
        Construct tornado HTTP "application" to run.
        """
        request_data: Dict[str, Any] = self.build_request_data()
        health_request_data: Dict[str, Any] = {
            "forwarded_request_metadata": self.forwarded_request_metadata
        }
        handlers = []
        handlers.append(("/", HealthCheckHandler, health_request_data))
        handlers.append(("/api/v1/list", ConciergeHandler, request_data))
        handlers.append(("/api/v1/docs", OpenApiPublishHandler, request_data))

        # Register templated request paths for agent API methods:
        # regexp format used here is that of Python Re standard library.
        handlers.append((r"/api/v1/([^/]+)/function", FunctionHandler, request_data))
        handlers.append((r"/api/v1/([^/]+)/connectivity", ConnectivityHandler, request_data))
        handlers.append((r"/api/v1/([^/]+)/streaming_chat", StreamingChatHandler, request_data))

        return HttpServerApp(handlers)

    def allow(self, agent_name) -> bool:
        return self.allowed_agents.get(agent_name, False)

    def update_agents(self, metadata: Dict[str, Any]):
        """
        Update list of agents for which serving is allowed.
        :param metadata: metadata to be used for logging if necessary.
        :return: nothing
        """
        data: Dict[str, Any] = {}
        session: ConciergeSession = DirectConciergeSession(metadata=metadata)
        agents_dict: Dict[str, List[Dict[str, str]]] = session.list(data)
        agents_list: List[Dict[str, str]] = agents_dict["agents"]
        agents: List[str] = []
        for agent_dict in agents_list:
            agents.append(agent_dict["agent_name"])
        with self.lock:
            # We assume all agents from "agents" list are enabled:
            for agent_name in agents:
                self.allowed_agents[agent_name] = True
            # All other agents are disabled:
            for agent_name, _ in self.allowed_agents.items():
                if agent_name not in agents:
                    self.allowed_agents[agent_name] = False

    def build_request_data(self) -> Dict[str, Any]:
        """
        Build request data for Http handlers.
        :return: a dictionary with request data to be passed to a http handler.
        """
        return {
            "agent_policy": self,
            "agents_updater": self,
            "port": self.port,
            "forwarded_request_metadata": self.forwarded_request_metadata,
            "openapi_service_spec_path": self.openapi_service_spec_path
        }
