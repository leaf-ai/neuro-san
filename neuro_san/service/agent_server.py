
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

from typing import Dict
from typing import List

import logging

from leaf_server_common.server.server_lifetime import ServerLifetime
from leaf_server_common.server.server_loop_callbacks import ServerLoopCallbacks

from neuro_san.api.grpc import agent_pb2
from neuro_san.api.grpc import concierge_pb2_grpc

from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.service.agent_server_logging import AgentServerLogging
from neuro_san.service.agent_servicer_to_server import AgentServicerToServer
from neuro_san.service.agent_service import AgentService
from neuro_san.service.concierge_service import ConciergeService
from neuro_san.session.chat_session_map import ChatSessionMap

DEFAULT_SERVER_NAME: str = 'neuro-san.Agent'
DEFAULT_SERVER_NAME_FOR_LOGS: str = 'Agent Server'
DEFAULT_MAX_CONCURRENT_REQUESTS: int = 10

# Better that we kill ourselves than kubernetes doing it for us
# in the middle of a request if there are resource leaks.
# This is per the lifetime of the server (before it kills itself).
DEFAULT_REQUEST_LIMIT: int = 1000 * 1000

# A space-delimited list of http metadata request keys to forward to logs/other requests
DEFAULT_FORWARDED_REQUEST_METADATA: str = "request_id user_id"


# pylint: disable=too-few-public-methods,too-many-instance-attributes
class AgentServer:
    """
    Server implementation for the Agent gRPC Service.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, port: int,
                 server_loop_callbacks: ServerLoopCallbacks,
                 chat_session_map: ChatSessionMap,
                 tool_registries: Dict[str, AgentToolRegistry],
                 server_name: str = DEFAULT_SERVER_NAME,
                 server_name_for_logs: str = DEFAULT_SERVER_NAME_FOR_LOGS,
                 max_concurrent_requests: int = DEFAULT_MAX_CONCURRENT_REQUESTS,
                 request_limit: int = DEFAULT_REQUEST_LIMIT,
                 forwarded_request_metadata: str = DEFAULT_FORWARDED_REQUEST_METADATA):
        """
        Constructor

        :param port: The integer port number for the service to listen on
        :param server_loop_callbacks: The ServerLoopCallbacks instance for
                break out methods in main serving loop.
        :param chat_session_map: The ChatSessionMap containing the global
                        map of session_id string to Agent
        :param tool_registries: A dictionary of agent name to AgentToolRegistry to use for the session.
        :param server_name: The name of the service
        :param server_name_for_logs: The name of the service for log files
        :param max_concurrent_requests: The maximum number of requests to handle at a time.
        :param request_limit: The number of requests to service before shutting down.
                        This is useful to be sure production environments can handle
                        a service occasionally going down.
        :param forwarded_request_metadata: A space-delimited list of http metadata request keys
                        to forward to logs/other requests
        """
        self.port = port
        self.server_loop_callbacks = server_loop_callbacks

        self.server_logging = AgentServerLogging(server_name_for_logs, forwarded_request_metadata)
        self.server_logging.setup_logging()

        self.logger = logging.getLogger(__name__)

        self.chat_session_map: ChatSessionMap = chat_session_map
        self.tool_registries: Dict[str, AgentToolRegistry] = tool_registries
        self.server_name: str = server_name
        self.server_name_for_logs: str = server_name_for_logs
        self.max_concurrent_requests: int = max_concurrent_requests
        self.request_limit: int = request_limit

        self.services: List[AgentService] = []

        self.logger.info("tool_registries found: %s", str(list(self.tool_registries.keys())))

    def get_services(self) -> List[AgentService]:
        """
        :return: A list of the AgentServices being served up by this instance
        """
        return self.services

    def serve(self):
        """
        Start serving gRPC requests
        """
        values = agent_pb2.DESCRIPTOR.services_by_name.values()
        server_lifetime = ServerLifetime(self.server_name,
                                         self.server_name_for_logs,
                                         self.port, self.logger,
                                         request_limit=self.request_limit,
                                         max_workers=self.max_concurrent_requests,
                                         max_concurrent_rpcs=None,
                                         # Used for health checking. Probably needs agent-specific love.
                                         protocol_services_by_name_values=values,
                                         loop_sleep_seconds=5.0,
                                         server_loop_callbacks=self.server_loop_callbacks)

        server = server_lifetime.create_server()

        # New-style service
        security_cfg = None     # ... yet

        for agent_name, tool_registry in self.tool_registries.items():

            service = AgentService(server_lifetime, security_cfg,
                                   self.chat_session_map,
                                   agent_name,
                                   tool_registry,
                                   self.server_logging)
            self.services.append(service)

            servicer_to_server = AgentServicerToServer(service, agent_name=agent_name)
            servicer_to_server.add_rpc_handlers(server)

        concierge_service: ConciergeService = \
            ConciergeService(server_lifetime,
                             security_cfg,
                             self.server_logging)
        concierge_pb2_grpc.add_ConciergeServiceServicer_to_server(
            concierge_service,
            server)

        server_lifetime.run()
