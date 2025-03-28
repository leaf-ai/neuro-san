from typing import Dict

from langchain_community.tools.bing_search import BingSearchResults
from langchain_community.utilities import BingSearchAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.agent_toolkits.openapi.toolkit import RequestsToolkit
from langchain_community.utilities.requests import TextRequestsWrapper
from langchain.tools import BaseTool


class BaseToolFactory:
    """
    A factory class for creating instances of various prebuilt tools.

    This class provides an interface to instantiate different tools based on the specified `tool_name`.
    The available tools include web search utilities and HTTP request utilities. This approach standardizes
    tool creation and simplifies integration with agents requiring predefined tools.

    ### Supported Tools:
    - **Search Tools:**
        - `"bing_search"`: Returns a `BingSearchResults` instance for performing Bing search queries.
        - `"tavily_search"`: Returns a `TavilySearchResults` instance for performing Tavily search queries.

    - **HTTP Request Tools:** These allow making different types of HTTP requests using the `RequestsToolkit`
      with a `TextRequestsWrapper`. The following tool names are available:
        - `"requests_get"`: For making GET requests.
        - `"requests_post"`: For making POST requests.
        - `"requests_patch"`: For making PATCH requests.
        - `"requests_put"`: For making PUT requests.
        - `"requests_delete"`: For making DELETE requests.

    ### Arguments:
    - `tool_name` (str): The name of the tool to instantiate. It determines which tool will be created.
    - `args` (Dict): A dictionary of keyword arguments passed to the tool's constructor.
                     The accepted arguments depend on the tool being instantiated. Some common ones include:
        - **Search Tools:**
          - `num_results` (int): Number of results to return (for Bing search).
          - `max_results` (int): Maximum number of results (for Tavily search).
        - **HTTP Request Tools:**
          - `headers` (Dict[str, str], optional): HTTP headers to include in the request.
          - `aiosession` (ClientSession, optional): Async session for making requests.
          - `auth` (Any, optional): Authentication credentials if required.
          - `response_content_type` (Literal["text", "json"], default="text"): Expected response format.

    ### Extending the Class:
    If additional tools need to be integrated, extend this class by adding appropriate conditions in the
    `get_agent_tool` method. Ensure that the tool name is unique and that required arguments are handled properly.

    **Note:** Future plans include providing a structured extensibility path for this factory class,
    allowing custom tools to be registered dynamically without modifying the core implementation.
    """

    def get_agent_tool(self, tool_name: str, args: Dict = None) -> BaseTool:
        """
        This method acts as a factory that dynamically creates and returns an instance of a supported tool.
        Depending on the specified `tool_name`, it initializes the corresponding tool with the provided arguments.

        :param: tool_name: name or key of the tool to use
        :param: args: arguments or parameters for class instantiation
        :return: Tool Class which is a subclass of Langchain's BaseTool class
        """
        if tool_name == "bing_search":
            # Some available args are
            # num_results: int
            return BingSearchResults(**args, api_wrapper=BingSearchAPIWrapper())

        if tool_name == "tavily_search":
            # Some available args are
            # max_results: int
            return TavilySearchResults(**args)

        if tool_name in ["requests_get", "requests_post", "requests_patch", "requests_put", "requests_delete"]:
            # Available args are
            # headers: Dict[str, str] | None = None,
            # aiosession: ClientSession | None = None,
            # auth: Any | None = None,
            # response_content_type: Literal['text', 'json'] = "text"
            request_toolkit = RequestsToolkit(
                requests_wrapper=TextRequestsWrapper(**args),
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

        raise ValueError(
            f"""Tool '{tool_name}' is not supported.
            Ensure that you have provided a valid tool name from the supported list:
            'bing_search', 'tavily_search', 'requests_get', 'requests_post', 'requests_patch', 'requests_put',
            'requests_delete'.

            If you are trying to use a different tool, you may need to implement support for it within
            the PrebuiltBaseToolFactory class. To do this, extend the `get_agent_tool` method
            by adding a corresponding condition for your new tool.

            Refer to the class documentation for more details on extending this functionality."""
        )
