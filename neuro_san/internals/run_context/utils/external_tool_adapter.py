
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
from typing import Any
from typing import Dict
from typing import List

import logging

from urllib.parse import ParseResult
from urllib.parse import urlparse

from grpc import StatusCode
from grpc.aio import AioRpcError

# The only reach-around from internals outward.
from neuro_san.session.agent_session import AgentSession
from neuro_san.session.async_service_agent_session import AsyncServiceAgentSession


class ExternalToolAdapter:
    """
    Class handles setting up a connection to an external agent server
    so that its agents can be used as tools.
    """

    def __init__(self, agent_url: str):
        """
        Constructor

        :param agent_url: The URL describing where to find the desired agent.
        """

        self.agent_url: str = agent_url
        self.session: AgentSession = None
        self.function_json: Dict[str, Any] = None

    async def get_function_json(self) -> Dict[str, Any]:
        """
        :return: The function json for the agent, as specified by the external agent.
        """
        if self.function_json is None:

            # Lazily get the information about the service
            agent_location: Dict[str, Any] = self.parse_external_agent(self.agent_url)
            self.session = self.create_session(agent_location)

            # Set up the request. Turns out we don't need much.
            request_dict: Dict[str, Any] = {}

            # Get the function spec so we can call it as a tool later.
            try:
                function_response: Dict[str, Any] = await self.session.function(request_dict)
                self.function_json = function_response.get("function")
            except AioRpcError as exception:
                message: str = f"Problem accessing external agent {self.agent_url}.\n"
                if exception.code() == StatusCode.UNIMPLEMENTED:
                    message += """
The server (which could be your own localhost) is currently not serving up
an agent network by that name. Try these hints:
1. Check to see that you do not have a typo in your reference to the external agent
   in the calling hocon file.
2. If you have control over the server, check to see that the agent network your are trying
   to reach has an entry in the manifest.hocon file whose value is set to true.
3. Consider restarting the server, as perhaps a server does not continually look
   for changes to hocon files or manifest files during normal operation.
4. If you are new to calling external agent networks, know that:
    a. Simply referencing an agent within your own hocon file with a / prefix
       does not mean the server is serving that agent up separately.
    b. Every agent that is externally referenceable needs its own hocon file
       which must also have an entry in the manifest.hocon file for the server.
    c. There is one and only one "front man" agent note in each network described
       by a hocon file that receives input on behalf of the network.
    d. In order to be called by external agents, that front man must have a full
       "function" definition, which includes a description, and at least one parameter
       defined.  These are how calling agents know how to interact with the agent network.
"""
                raise ValueError(message) from exception

        return self.function_json

    @staticmethod
    def parse_external_agent(agent_url: str) -> Dict[str, str]:
        """
        :param agent_url: The URL describing where to find the desired agent.
        :return: A Dictionary with the following keys:
                "host" - the hostname where the agent lives
                "port" - the port on the host which serves up the agent (if any)
                "agent_name" - the name of the agent on that host

                OR

                None if the parsing of the agent_url was unsuccessful.
        """
        if agent_url is None or len(agent_url) == 0:
            return None

        parse_result: ParseResult = urlparse(agent_url)
        if parse_result is None:
            return None

        if parse_result.path is None or len(parse_result.path) <= 1:
            # We don't have enough characters in the path to even specify
            # an agent that lives on the same server.
            return None

        if not parse_result.path.startswith("/"):
            # This is not an external agent specification
            return None

        host: str = None
        port: str = None
        if len(parse_result.netloc) > 0:
            # We have a host specified
            split: List[str] = parse_result.netloc.split(":")
            host = split[0]
            if len(split) > 1:
                port = split[0]

        # Special case for detecting localhost
        if host is None or len(host) == 0:
            host = "localhost"

        # Get the agent name from the URL by looking at the path
        # Remove any leading slashes from the path for the agent name.
        # Note: While we need to get the agent name for proper gRPC routing,
        #       this is not yet super robust against any non-default case
        #       where some other entity needs a non-standard path for routing
        #       (like a load balancer).  Cross that bridge when we get to it.
        agent_name: str = parse_result.path
        while agent_name.startswith("/"):
            agent_name = agent_name[1:]

        # Assemble the return dictionary
        return_dict = {
            "host": host,
            "port": port,
            "agent_name": agent_name,
            # DEF: At some point, get this from the parsing and/or config/defaults.
            "service_prefix": None
        }
        return return_dict

    @staticmethod
    def is_external_agent(agent_url: str) -> bool:
        """
        :param agent_url: The URL describing where to find the desired agent.
        :return: True if the given string is interpretable as an agent url
                (without actually connecting to it).  False otherwise.
        """
        agent_location: Dict[str, str] = ExternalToolAdapter.parse_external_agent(agent_url)
        is_external: bool = agent_location is not None
        return is_external

    @staticmethod
    def get_safe_agent_name(agent_url: str) -> str:
        """
        :param agent_url: The URL describing where to find the desired agent.
        :return: A name that is suitable for using within agent toolkits (like langchain)
                for internal tool reference.
        """
        safe_name: str = agent_url
        if ExternalToolAdapter.is_external_agent(agent_url):

            agent_location: Dict[str, str] = ExternalToolAdapter.parse_external_agent(agent_url)

            # FWIW: langchain internal tool references must satisfy the regex: "^[a-zA-Z0-9_-]+$"
            # It's possible that more complex external references might have the agent_name
            # needing futher mangling.  Cross that bridge when we have a real example.
            safe_name = "__" + agent_location.get("agent_name")

        return safe_name

    @staticmethod
    def create_session(agent_location: Dict[str, str]) -> AgentSession:
        """
        :param agent_location: An agent location dictionary returned by parse_external_agent()
        :return: An AgentSession through which communications about the external agent can be made.
        """
        if agent_location is None:
            return None

        # Create the session.
        host = agent_location.get("host")
        port = agent_location.get("port")
        agent_name = agent_location.get("agent_name")
        service_prefix = agent_location.get("service_prefix")

        # Optimization:
        #   It's possible we might want to create a different kind of session
        #   to minimize socket usage, but for now use the AsyncServiceAgentSession
        #   so as to ensure proper logging even on the same server (localhost).
        session = AsyncServiceAgentSession(host, port, agent_name=agent_name,
                                           service_prefix=service_prefix)

        # Quiet any logging from leaf-common grpc stuff.
        quiet_please = logging.getLogger("leaf_common.session.grpc_client_retry")
        quiet_please.setLevel(logging.WARNING)

        return session
