
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

import logging

import os

from argparse import ArgumentParser
from pathlib import Path

from leaf_common.asyncio.asyncio_executor import AsyncioExecutor
from leaf_server_common.server.server_loop_callbacks import ServerLoopCallbacks

from neuro_san.internals.chat.chat_session import ChatSession
from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.internals.graph.registry.agent_tool_registry_restorer import AgentToolRegistryRestorer
from neuro_san.internals.utils.file_of_class import FileOfClass
from neuro_san.service.agent_server import AgentServer
from neuro_san.service.agent_server import DEFAULT_SERVER_NAME
from neuro_san.service.agent_server import DEFAULT_SERVER_NAME_FOR_LOGS
from neuro_san.service.agent_server import DEFAULT_REQUEST_LIMIT
from neuro_san.service.agent_service import AgentService
from neuro_san.service.registry_manifest_restorer import RegistryManifestRestorer
from neuro_san.session.agent_service_stub import DEFAULT_SERVICE_PREFIX
from neuro_san.session.agent_session import AgentSession
from neuro_san.session.chat_session_map import ChatSessionMap

# A *single* global variable which contains a mapping of
# string keys -> ChatSession implementations
CHAT_SESSIONS: Dict[str, ChatSession] = {}

# A single global for executing asyncio stuff in the background
ASYNCIO_EXECUTOR: AsyncioExecutor = AsyncioExecutor()


# pylint: disable=too-many-instance-attributes
class AgentMainLoop(ServerLoopCallbacks):
    """
    This class handles the service main loop.
    """

    DEFAULT_TOOL_REGISTRY_FILE: str = "esp_decision_assistant.hocon"

    def __init__(self, service_prefix: str = DEFAULT_SERVICE_PREFIX):
        """
        Constructor

        :param service_prefix: An optional prefix that gets prepended to all gRPC request/response
                        handling for this instance of the server. Note that this can be
                        passed in by argument (as opposed to env var) because this is the
                        one configurable item that is likely to be shared with other code.
        """
        self.port: int = 0
        self.asyncio_executor = ASYNCIO_EXECUTOR

        # Points to the global
        init_arguments = {
            "chat_sessions": CHAT_SESSIONS,
            "executor": ASYNCIO_EXECUTOR
        }
        self.chat_session_map = ChatSessionMap(init_arguments)
        self.tool_registries: Dict[str, AgentToolRegistry] = {}

        self.server_name: str = DEFAULT_SERVER_NAME
        self.server_name_for_logs: str = DEFAULT_SERVER_NAME_FOR_LOGS
        self.request_limit: int = DEFAULT_REQUEST_LIMIT
        self.service_prefix: str = service_prefix
        self.server: AgentServer = None

    def parse_args(self):
        """
        Parse command-line arguments into member variables
        """
        # Set up the CLI parser
        arg_parser = ArgumentParser()

        # If we are using a manifest file, allow all the tools in the manifest
        default_tool_registry_file: str = ""
        if os.environ.get("AGENT_MANIFEST_FILE") is None:
            # If there is no manifest, then fall back to a default
            default_tool_registry_file = self.DEFAULT_TOOL_REGISTRY_FILE

        arg_parser.add_argument("--tool_registry_file", type=str,
                                default=default_tool_registry_file,
                                help=".hocon or .json file defining the AgentToolRegistry for the service")
        arg_parser.add_argument("--port", type=int,
                                default=int(os.environ.get("AGENT_PORT", AgentSession.DEFAULT_PORT)),
                                help="Port number for the service")
        arg_parser.add_argument("--server_name", type=str,
                                default=str(os.environ.get("AGENT_SERVER_NAME", self.server_name)),
                                help="Name of the service")
        arg_parser.add_argument("--server_name_for_logs", type=str,
                                default=str(os.environ.get("AGENT_SERVER_NAME_FOR_LOGS", self.server_name_for_logs)),
                                help="Name of the service as seen in logs")
        arg_parser.add_argument("--service_prefix", type=str,
                                default=str(os.environ.get("AGENT_SERVICE_PREFIX", self.service_prefix)),
                                help="Name of the service as seen in logs")
        arg_parser.add_argument("--request_limit", type=int,
                                default=int(os.environ.get("AGENT_REQUEST_LIMIT", self.request_limit)),
                                help="Number of requests served before the server shuts down in an orderly fashion")

        # Actually parse the args into class variables

        # Incorrectly flagged as Path Traversal 3, 7
        # See destination below ~ line 139, 154 for explanation.
        args = arg_parser.parse_args()
        self.port = args.port
        self.server_name = args.server_name
        self.server_name_for_logs = args.server_name_for_logs
        self.service_prefix = args.service_prefix
        self.request_limit = args.request_limit

        manifest_restorer = RegistryManifestRestorer()
        manifest_tool_registries: Dict[str, AgentToolRegistry] = manifest_restorer.restore()

        registry_name: str = None
        tool_registry: AgentToolRegistry = None
        tool_registry_file: str = args.tool_registry_file
        if tool_registry_file is not None and len(tool_registry_file) > 0:
            # Check the path to avoid Path Traversal issues from scans.
            tool_registry_file = FileOfClass.check_file(tool_registry_file, basis="~")

            # Incorrectly flagged as destination of Path Traversal 3
            #   Reason: This is the method in which we are actually trying to do
            #           the path traversal check itself. CheckMarx does not recognize
            #           the call to check_file as a valid means to resolve these kinds
            #           of issues.
            registry_name = Path(tool_registry_file).stem
            tool_registry = manifest_tool_registries.get(registry_name)

        found_status: str = ""
        if tool_registry is None and registry_name is not None:
            # Not found in the registry. Maybe it wasn't updated.
            # Look for the file in the registries area.
            this_file_dir: str = Path(__file__).parent.resolve()
            registry_dir: str = (Path(this_file_dir) / ".." / "registries").resolve()

            # Inside here is incorrectly flagged as destination of Path Traversal 7
            #   Reason: The lines above ensure that the path of registry_dir is within
            #           this source base. CheckMarx does not recognize
            #           the calls to Pathlib/__file__  as a valid means to resolve
            #           these kinds of issues.
            registry_restorer = AgentToolRegistryRestorer(registry_dir)
            tool_registry_file = FileOfClass.check_file(tool_registry_file, basis=registry_dir)
            tool_registry = registry_restorer.restore(file_reference=tool_registry_file)

        if tool_registry is not None:
            # If a tool_registry was found, only prepare one.
            self.tool_registries = {
                registry_name: tool_registry
            }
            print(f"Single tool_registry {registry_name} {found_status} found")
        else:
            self.tool_registries = manifest_tool_registries
            print(f"tool_registries found: {list(self.tool_registries.keys())}")

    def main_loop(self):
        """
        Command line entry point
        """
        self.parse_args()

        # Start up the background thread which will process asyncio stuff
        self.asyncio_executor.start()

        self.server = AgentServer(self.port,
                                  server_loop_callbacks=self,
                                  chat_session_map=self.chat_session_map,
                                  tool_registries=self.tool_registries,
                                  asyncio_executor=self.asyncio_executor,
                                  server_name=self.server_name,
                                  server_name_for_logs=self.server_name_for_logs,
                                  request_limit=self.request_limit,
                                  service_prefix=self.service_prefix)
        self.server.serve()

    def loop_callback(self) -> bool:
        """
        Periodically called by the main server loop of ServerLifetime.
        """
        self.chat_session_map.prune()

        # Report back on service activity so the ServerLifetime that calls
        # this method can properly yield/sleep depending on how many requests
        # are in motion.
        agent_services: List[AgentService] = self.server.get_services()
        for agent_service in agent_services:
            if agent_service.get_request_count() > 0:
                return True

        return False

    def shutdown_callback(self):
        """
        Called by the main server loop when it's time to shut down.
        """
        logger = logging.getLogger(self.__class__.__name__)

        logger.info("Shutdown: cleaning up ChatSessionMap")
        self.chat_session_map.cleanup()

        logger.info("Shutdown: shutting down AsyncioExecutor")
        self.asyncio_executor.shutdown()


if __name__ == '__main__':
    AgentMainLoop().main_loop()
