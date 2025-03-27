from langchain_community.tools.bing_search import BingSearchResults
from langchain_community.utilities import BingSearchAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.agent_toolkits.openapi.toolkit import RequestsToolkit
from langchain_community.utilities.requests import TextRequestsWrapper


class PrebuiltBaseToolFactory:
    """
    A factory class that returns prebuilt tools based on the provided tool name.

    This class allows for the creation of various tool instances based on the `tool_name` argument passed during
    instantiation. The available tools include search and HTTP request-related tools, such as:

    - "bing_search": Returns a `BingSearchResults` instance for performing Bing search queries.
    - "tavily_search": Returns a `TavilySearchResults` instance for performing Tavily search queries.
    - HTTP request tools: Includes tools for making HTTP requests, such as GET, POST, PATCH, PUT, and DELETE requests,
      using the `RequestsToolkit` with a `TextRequestsWrapper`. The tool names are mapped as:
        - "requests_get": For making GET requests.
        - "requests_post": For making POST requests.
        - "requests_patch": For making PATCH requests.
        - "requests_put": For making PUT requests.
        - "requests_delete": For making DELETE requests.

    Args:
        tool_name (str): The name of the tool to instantiate. This determines which specific tool will be created.
        **kwargs: Additional keyword arguments that are passed to the tool's constructor. The accepted arguments
                  depend on the tool being created (e.g., `num_results`, `max_results`, `auth`, `headers`).

    Note:
        To add more tools, you should extend this class by adding additional `if` conditions
        in the `__new__` method for each new tool. Each tool should have a unique `tool_name`
        and appropriate handling for its initialization, including any expected arguments.
    """
    def __new__(cls, tool_name: str, **kwargs):
        if tool_name == "bing_search":
            # Some available args are
            # num_results: int
            return BingSearchResults(api_wrapper=BingSearchAPIWrapper(), **kwargs)

        if tool_name == "tavily_search":
            # Some available args are
            # max_results: int
            return TavilySearchResults(**kwargs)

        if tool_name in ["requests_get", "requests_post", "requests_patch", "requests_put", "requests_delete"]:
            # Some available args are
            # auth: Any
            # headers: Dict[str, str]
            request_toolkit = RequestsToolkit(
                requests_wrapper=TextRequestsWrapper(**kwargs),
                allow_dangerous_requests=True,
            )
            request_tools = request_toolkit.get_tools()
            mapping = {
                "requests_get": request_tools[0],
                "requests_post": request_tools[1],
                "requests_patch": request_tools[2],
                "requests_put": request_tools[3],
                "requests_delete": request_tools[4],
            }
            return mapping[tool_name]

        raise ValueError(f"Tool '{tool_name}' is not supported.")
