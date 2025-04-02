
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
from typing import Type

import os

from langchain.tools import BaseTool

from leaf_common.config.dictionary_overlay import DictionaryOverlay
from leaf_common.config.resolver import Resolver

from neuro_san.internals.run_context.langchain.base_tool_info_restorer import BaseToolInfoRestorer


class BaseToolFactory:
    """
    A factory class for creating instances of various prebuilt tools.

    This class provides an interface to instantiate different tools based on the specified `base_tool`.
    The available tools include web search utilities and HTTP request utilities. This approach standardizes
    tool creation and simplifies integration with agents requiring predefined tools.

    ### Supported Tools:
    - **Search Tools:**
        - `bing_search`: Returns a `BingSearchResults` instance for performing Bing search queries.
        - `tavily_search`: Returns a `TavilySearchResults` instance for performing Tavily search queries.

    - **HTTP Request Tools:** These allow making different types of HTTP requests using the `RequestsToolkit`
      with a `TextRequestsWrapper`. The following tool names are available:
        - `requests_get`: For making GET requests.
        - `requests_post`: For making POST requests.
        - `requests_patch`: For making PATCH requests.
        - `requests_put`: For making PUT requests.
        - `requests_delete`: For making DELETE requests.

    ### Arguments:
    - `base_tool` (str): The name of the tool to instantiate. It determines which tool will be created.
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

    ### Extending the Class

        To integrate additional tools, add a tool configuration file in JSON or HOCON format
        and set its path to the environment variable `BASE_TOOL_INFO_FILE`.

        The configuration should follow this structure:
        - The tool name serves as a key.
        - The corresponding value should be a dictionary with:
        - `class`: The fully qualified class name of the tool.
        - `args`: A dictionary of arguments required for the tool's initialization,
            which may include nested class configurations.

        The default prebuilt tool config file can be seen at
        'neuro_san/internals/run_context/langchain/base_tool_info.hocon'

    **Note:**
    Future updates will introduce support for integrating custom `CodedTool`
    implementations and Langchain’s `BaseToolKit` into this factory.
    """

    def __init__(self):
        """
        Constructor
        """
        self.base_tool_infos: Dict[str, Any] = {}
        self.overlayer = DictionaryOverlay()
        self.base_tool_info_file: str = None

    def load(self):
        """
        Loads the base tool information from hocon files.
        """
        restorer = BaseToolInfoRestorer()
        self.base_tool_infos = restorer.restore()

        # Mix in user-specified base_tool info, if available.
        base_tool_info_file: str = os.getenv("BASE_TOOL_INFO_FILE")
        if base_tool_info_file is not None and len(base_tool_info_file) > 0:
            extra_base_tool_infos: Dict[str, Any] = restorer.restore(file_reference=base_tool_info_file)
            self.base_tool_infos = self.overlayer.overlay(self.base_tool_infos, extra_base_tool_infos)

            self.base_tool_info_file = base_tool_info_file

    def create_agent_tool(self, tool_name: str, user_args: Dict[str, Any] = None) -> BaseTool:
        """
        Resolves dependencies and instantiates the requested tool.

        :param tool_name: The name of the tool to instantiate.
        :param user_args: Arguments provided by the user, which override the config file.
        :return: The instantiated tool.
        """
        tool_info: Dict = self.base_tool_infos.get(tool_name)
        if not tool_info:
            raise ValueError(f"Tool '{tool_name}' is not defined in {self.base_tool_info_file}.")

        if not isinstance(tool_info, Dict):
            raise ValueError(f"The value for the {tool_name} key must be a dictionary.")

        # Recursively resolve arguments (including dependencies)
        resolved_args: Dict = self._resolve_args(tool_info.get("args", {}))

        # Merge with user arguments where user_args get the priority
        if user_args:
            final_args: Dict = self.overlayer.overlay(resolved_args, user_args)
        else:
            final_args = resolved_args

        # Instantiate the main tool class
        tool_class: Type[BaseTool] = self._resolve_class(tool_info["class"])
        return tool_class(**final_args)

    def _resolve_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursive resolves arguments when there is a wrapper class as an argument,
        otherwise return args as a dictionary.

        :param args: The arguments to resolve.
        :return: A dictionary of resolved arguments.
        """
        resolved_args = {}
        for key, value in args.items():
            if isinstance(value, dict) and "class" in value:
                # If the argument is a class definition, resolve and instantiate it
                nested_class = self._resolve_class(value["class"])
                nested_args = self._resolve_args(value.get("args", {}))
                resolved_args[key] = nested_class(**nested_args)
            else:
                # Otherwise, keep primitive values as they are
                resolved_args[key] = value
        return resolved_args

    def _resolve_class(self, class_path: str) -> Type[BaseTool]:
        """
        Uses Resolver to dynamically import a class.

        :param class_path: Full class path (e.g., "package.module.ClassName").
        :return: The resolved class type.
        """
        class_split: List[str] = class_path.split(".")
        if len(class_split) <= 2:
            raise ValueError(
                f"Value in 'class' in {self.base_tool_info_file} must be of the form "
                "'<package_name>.<module_name>.<ClassName>'"
            )

        # Extract module and class details
        packages: List[str] = [".".join(class_split[:-2])]
        class_name: str = class_split[-1]
        resolver = Resolver(packages)

        # Resolve class
        try:
            return resolver.resolve_class_in_module(class_name, module_name=class_split[-2])
        except AttributeError as exception:
            raise ValueError(f"Class {class_path} not found in PYTHONPATH") from exception
