from typing import Any
from typing import Dict
from typing import List

from urllib.parse import ParseResult
from urllib.parse import urlparse

from neuro_san.session.agent_session import AgentSession
from neuro_san.session.service_agent_session import ServiceAgentSession


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

            # Lazily get the information from the service
            agent_location: Dict[str, Any] = self.parse_external_agent(self.agent_url)
            self.session = self.create_session(agent_location)

            # Set up the request. Turns out we don't need much.
            request_dict: Dict[str, Any] = {}

            # Ideally this guy would be async as well.
            function_response: Dict[str, Any] = self.session.function(request_dict)
            self.function_json = function_response.get("function")

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
            "agent_name": agent_name
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
        return agent_location is not None

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

        # Optimization:
        #   It's possible we might want to create a different kind of session
        #   to minimize socket usage, but for now use the ServiceAgentSession
        #   so as to ensure proper logging even on the same server (localhost).
        session = ServiceAgentSession(host, port, agent_name=agent_name)
        return session
