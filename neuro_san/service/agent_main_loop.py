
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
from typing import Dict
from typing import List

import multiprocessing
import os

from argparse import ArgumentParser

from leaf_server_common.server.server_loop_callbacks import ServerLoopCallbacks

from neuro_san.interfaces.agent_session import AgentSession
from neuro_san.internals.graph.persistence.registry_manifest_restorer import RegistryManifestRestorer
from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.service.agent_server import AgentServer
from neuro_san.service.agent_server import DEFAULT_SERVER_NAME
from neuro_san.service.agent_server import DEFAULT_SERVER_NAME_FOR_LOGS
from neuro_san.service.agent_server import DEFAULT_MAX_CONCURRENT_REQUESTS
from neuro_san.service.agent_server import DEFAULT_REQUEST_LIMIT
from neuro_san.service.agent_server import DEFAULT_FORWARDED_REQUEST_METADATA
from neuro_san.service.agent_service import AgentService
from neuro_san.http_sidecar.http_sidecar import HttpSidecar


# pylint: disable=too-many-instance-attributes
class AgentMainLoop(ServerLoopCallbacks):
    """
    This class handles the service main loop.
    """

    def __init__(self):
        """
        Constructor
        """
        self.port: int = 0
        self.http_port: int = 0

        self.tool_registries: Dict[str, AgentToolRegistry] = {}

        self.server_name: str = DEFAULT_SERVER_NAME
        self.server_name_for_logs: str = DEFAULT_SERVER_NAME_FOR_LOGS
        self.max_concurrent_requests: int = DEFAULT_MAX_CONCURRENT_REQUESTS
        self.request_limit: int = DEFAULT_REQUEST_LIMIT
        self.forwarded_request_metadata: int = DEFAULT_FORWARDED_REQUEST_METADATA
        self.server: AgentServer = None

    def parse_args(self):
        """
        Parse command-line arguments into member variables
        """
        # Set up the CLI parser
        arg_parser = ArgumentParser()

        arg_parser.add_argument("--port", type=int,
                                default=int(os.environ.get("AGENT_PORT", AgentSession.DEFAULT_PORT)),
                                help="Port number for the grpc service")
        arg_parser.add_argument("--http_port", type=int,
                                default=int(os.environ.get("AGENT_HTTP_PORT", AgentSession.DEFAULT_HTTP_PORT)),
                                help="Port number for http service endpoint")
        arg_parser.add_argument("--server_name", type=str,
                                default=str(os.environ.get("AGENT_SERVER_NAME", self.server_name)),
                                help="Name of the service for health reporting purposes.")
        arg_parser.add_argument("--server_name_for_logs", type=str,
                                default=str(os.environ.get("AGENT_SERVER_NAME_FOR_LOGS", self.server_name_for_logs)),
                                help="Name of the service as seen in logs")
        arg_parser.add_argument("--max_concurrent_requests", type=int,
                                default=int(os.environ.get("AGENT_MAX_CONCURRENT_REQUESTS",
                                                           self.max_concurrent_requests)),
                                help="Maximm number of requests that can be served at the same time")
        arg_parser.add_argument("--request_limit", type=int,
                                default=int(os.environ.get("AGENT_REQUEST_LIMIT", self.request_limit)),
                                help="Number of requests served before the server shuts down in an orderly fashion")
        arg_parser.add_argument("--forwarded_request_metadata", type=str,
                                default=os.environ.get("AGENT_FORWARDED_REQUEST_METADATA",
                                                       self.forwarded_request_metadata),
                                help="Space-delimited list of http request metadata keys to forward "
                                     "to logs/other requests")

        # Actually parse the args into class variables

        # Incorrectly flagged as Path Traversal 3, 7
        # See destination below ~ line 139, 154 for explanation.
        args = arg_parser.parse_args()
        self.port = args.port
        self.http_port = args.http_port
        self.server_name = args.server_name
        self.server_name_for_logs = args.server_name_for_logs
        self.max_concurrent_requests = args.max_concurrent_requests
        self.request_limit = args.request_limit
        self.forwarded_request_metadata = args.forwarded_request_metadata

        manifest_restorer = RegistryManifestRestorer()
        manifest_tool_registries: Dict[str, AgentToolRegistry] = manifest_restorer.restore()

        self.tool_registries = manifest_tool_registries

    def main_loop(self):
        """
        Command line entry point
        """
        self.parse_args()

        self.server = AgentServer(self.port,
                                  server_loop_callbacks=self,
                                  tool_registries=self.tool_registries,
                                  server_name=self.server_name,
                                  server_name_for_logs=self.server_name_for_logs,
                                  max_concurrent_requests=self.max_concurrent_requests,
                                  request_limit=self.request_limit,
                                  forwarded_request_metadata=self.forwarded_request_metadata)

        # Start HTTP server side-car:
        http_sidecar = HttpSidecar(
            self.port,
            self.http_port,
            self.tool_registries,
            forwarded_request_metadata=self.forwarded_request_metadata)
        http_server_process = multiprocessing.Process(target=http_sidecar)
        http_server_process.start()

        try:
            self.server.serve()
        finally:
            http_server_process.terminate()
            http_server_process.join()

    def loop_callback(self) -> bool:
        """
        Periodically called by the main server loop of ServerLifetime.
        """
        # Report back on service activity so the ServerLifetime that calls
        # this method can properly yield/sleep depending on how many requests
        # are in motion.
        agent_services: List[AgentService] = self.server.get_services()
        for agent_service in agent_services:
            if agent_service.get_request_count() > 0:
                return True

        return False


if __name__ == '__main__':
    AgentMainLoop().main_loop()
