
# Copyright (C) 2023-2024 Cognizant Digital Business, Evolutionary AI.
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

import logging

from os import environ

from argparse import ArgumentParser
from pathlib import Path

from leaf_server_common.server.server_loop_callbacks \
    import ServerLoopCallbacks

from neuro_san.chat.chat_session import ChatSession
from neuro_san.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.graph.registry.agent_tool_registry_restorer import AgentToolRegistryRestorer
from neuro_san.service.agent_server import AgentServer
from neuro_san.service.registry_manifest_restorer import RegistryManifestRestorer
from neuro_san.session.asyncio_executor import AsyncioExecutor
from neuro_san.session.chat_session_map import ChatSessionMap
from neuro_san.session.agent_session import AgentSession

# A *single* global variable which contains a mapping of
# string keys -> ChatSession implementations
CHAT_SESSIONS: Dict[str, ChatSession] = {}

# A single global for executing asyncio stuff in the background
ASYNCIO_EXECUTOR: AsyncioExecutor = AsyncioExecutor()


class AgentMainLoop(ServerLoopCallbacks):
    """
    This class handles the service main loop.
    """

    DEFAULT_TOOL_REGISTRY_FILE: str = "esp_decision_assistant.hocon"

    def __init__(self):
        """
        Constructor
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

    def parse_args(self):
        """
        Parse command-line arguments into member variables
        """
        # Set up the CLI parser
        arg_parser = ArgumentParser()
        arg_parser.add_argument("--tool_registry_file", type=str,
                                default=self.DEFAULT_TOOL_REGISTRY_FILE,
                                help=".hocon or .json file defining the AgentToolRegistry for the service")
        arg_parser.add_argument("--port", type=int,
                                default=int(environ.get("DECISION_ASSISTANT_PORT",
                                                        AgentSession.DEFAULT_PORT)),
                                help="Port number for the service")

        # Actually parse the args into class variables
        args = arg_parser.parse_args()
        self.port = args.port

        manifest_restorer = RegistryManifestRestorer()
        manifest_tool_registries: Dict[str, AgentToolRegistry] = manifest_restorer.restore()

        registry_name: str = None
        tool_registry: AgentToolRegistry = None
        tool_registry_file: str = args.tool_registry_file
        if tool_registry_file is not None and len(tool_registry_file) > 0:
            registry_name = Path(tool_registry_file).stem
            tool_registry = manifest_tool_registries.get(registry_name)

        found_status: str = ""
        if tool_registry is None and registry_name is not None:
            # Not found in the registry. Maybe it wasn't updated.
            # Look for the file in the registries area.
            this_file_dir: str = Path(__file__).parent.resolve()
            registry_dir: str = (Path(this_file_dir) / ".." / "registries").resolve()
            registry_restorer = AgentToolRegistryRestorer(registry_dir)
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

        grpc_server = AgentServer(self.port,
                                  server_loop_callbacks=self,
                                  chat_session_map=self.chat_session_map,
                                  tool_registries=self.tool_registries,
                                  asyncio_executor=self.asyncio_executor)
        grpc_server.serve()

    def loop_callback(self):
        """
        Periodically called by the main server loop of ServerLifetime.
        """
        self.chat_session_map.prune()

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
