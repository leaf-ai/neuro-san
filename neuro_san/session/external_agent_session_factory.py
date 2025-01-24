
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

import logging

from neuro_san.internals.graph.registry.agent_tool_registry import AgentToolRegistry
from neuro_san.internals.run_context.interfaces.async_agent_session_factory import AsyncAgentSessionFactory
from neuro_san.internals.run_context.interfaces.invocation_context import InvocationContext
from neuro_san.internals.run_context.utils.external_agent_parsing import ExternalAgentParsing
from neuro_san.session.async_direct_agent_session import AsyncDirectAgentSession
from neuro_san.session.async_service_agent_session import AsyncServiceAgentSession
from neuro_san.session.agent_session import AgentSession


class ExternalAgentSessionFactory(AsyncAgentSessionFactory):
    """
    Creates AgentSessions for external agents.
    """

    def __init__(self, use_direct: bool = False):
        """
        Constructuor

        :param use_direct: When True, will use a Direct session for
                    external agents that would reside on the same server.
        """
        self.use_direct: bool = use_direct

    def create_session(self, agent_url: str,
                       invocation_context: InvocationContext) -> AgentSession:
        """
        :param agent_url: A url string pointing to an external agent that came from
                    a tools list in an agent spec.
        :param invocation_context: The context policy container that pertains to the invocation
                    of the agent.
        :return: An AgentSession through which communications about the external agent can be made.
        """

        agent_location: Dict[str, str] = ExternalAgentParsing.parse_external_agent(agent_url)
        session = self.create_session(agent_location, invocation_context)
        return session

    def create_session_from_location_dict(self, agent_location: Dict[str, str],
                                          invocation_context: InvocationContext) -> AgentSession:
        """
        :param agent_location: An agent location dictionary returned by
                    ExternalAgentParsing.parse_external_agent()
        :param invocation_context: The context policy container that pertains to the invocation
                    of the agent.
        :return: An AgentSession through which communications about the external agent can be made.
        """
        if agent_location is None:
            return None

        # Create the session.
        host = agent_location.get("host")
        port = agent_location.get("port")
        agent_name = agent_location.get("agent_name")
        service_prefix = agent_location.get("service_prefix")

        session: AgentSession = None
        if self.use_direct and (host is None or len(host) == 0 or host == "localhost"):
            # Optimization: We want to create a different kind of session to minimize socket usage
            # and potentially relieve the direct user of the burden of having to start a server

            chat_session_map = None
            tool_registry: AgentToolRegistry = None     # DEF make this real
            session = AsyncDirectAgentSession(chat_session_map, tool_registry, invocation_context)

        if session is None:
            session = AsyncServiceAgentSession(host, port, agent_name=agent_name,
                                               service_prefix=service_prefix)

        # Quiet any logging from leaf-common grpc stuff.
        quiet_please = logging.getLogger("leaf_common.session.grpc_client_retry")
        quiet_please.setLevel(logging.WARNING)

        return session
