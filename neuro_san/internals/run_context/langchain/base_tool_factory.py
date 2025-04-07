
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

from inspect import signature
from types import MethodType
from typing import Any
from typing import Dict
from typing import List
from typing import Set
from typing import Type
from typing import Union

import os

from langchain.tools import BaseTool
from langchain_community.agent_toolkits.base import BaseToolkit
from pydantic import BaseModel

from leaf_common.config.dictionary_overlay import DictionaryOverlay
from leaf_common.config.resolver import Resolver

from neuro_san.internals.interfaces.context_type_base_tool_factory import ContextTypeBaseToolFactory
from neuro_san.internals.run_context.langchain.base_tool_info_restorer import BaseToolInfoRestorer


class BaseToolFactory(ContextTypeBaseToolFactory):
    """
    A factory class for creating instances of various prebuilt tools.

    This class provides an interface to instantiate different tools based on the specified "base_tool".
    The available tools include web search utilities and HTTP request utilities. This approach standardizes
    tool creation and simplifies integration with agents requiring predefined tools.

    ### Supported Tools:
    - **Search Tools:**
        - "bing_search": Returns a "BingSearchResults" instance for performing Bing search queries.
        - "tavily_search": Returns a "TavilySearchResults" instance for performing Tavily search queries.

    - **HTTP Request Tools:** These allow making different types of HTTP requests using the "RequestsToolkit"
      with a "TextRequestsWrapper". The following tool names are available:
        - "requests_get": For making GET requests.
        - "requests_post": For making POST requests.
        - "requests_patch": For making PATCH requests.
        - "requests_put": For making PUT requests.
        - "requests_delete": For making DELETE requests.
        - "requests_toolkit": For all of the above request tools.

    ### Arguments:
    - "tool_name" (str): The name of the tool to instantiate. It determines which tool will be created.
    - "user_args" (Dict): A dictionary of keyword arguments passed to the tool's constructor.
                     The accepted arguments depend on the tool being instantiated. Some common ones include:
        - **Search Tools:**
          - "num_results" (int): Number of results to return (for Bing search).
          - "max_results" (int): Maximum number of results (for Tavily search).
        - **HTTP Request Tools:**
          - "headers" (Dict[str, str], optional): HTTP headers to include in the request.
          - "aiosession" (ClientSession, optional): Async session for making requests.
          - "auth" (Any, optional): Authentication credentials if required.
          - "response_content_type" (Literal["text", "json"], default="text"): Expected response format.

    ### Extending the Class

        To integrate additional tools, add a tool configuration file in JSON or HOCON format
        and set its path to the environment variable "AGENT_BASE_TOOL_INFO_FILE".

        The configuration should follow this structure:
        - The tool name serves as a key.
        - The corresponding value should be a dictionary with:
        - "class": The fully qualified class name of the tool.
        - "args": A dictionary of arguments required for the tool's initialization,
            which may include nested class configurations.

        The default prebuilt tool config file can be seen at
        "neuro_san/internals/run_context/langchain/base_tool_info.hocon"

    **Note:**
    Future updates will introduce support for integrating custom "CodedTool"
    implementations and Langchain’s "BaseToolKit" into this factory.
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
        base_tool_info_file: str = os.getenv("AGENT_BASE_TOOL_INFO_FILE")
        if base_tool_info_file is not None and len(base_tool_info_file) > 0:
            extra_base_tool_infos: Dict[str, Any] = restorer.restore(file_reference=base_tool_info_file)
            self.base_tool_infos = self.overlayer.overlay(self.base_tool_infos, extra_base_tool_infos)

            self.base_tool_info_file = base_tool_info_file

    def create_base_tool(self, tool_name: str, user_args: Dict[str, Any] = None) -> Union[BaseTool, List[BaseTool]]:
        """
        Resolves dependencies and instantiates the requested tool.

        :param tool_name: The name of the tool to instantiate.
        :param user_args: Arguments provided by the user, which override the config file.
        :return: - Instantiated tool if "class" of tool_name points to a BaseTool class
                 - A list of tools if "class of "tool_name points to a BaseToolkit class.
        """
        empty: Dict[str, Any] = {}

        tool_info: Dict[str, Any] = self.base_tool_infos.get(tool_name)
        if not tool_info:
            raise ValueError(f"Tool '{tool_name}' is not defined in {self.base_tool_info_file}.")

        if not isinstance(tool_info, Dict):
            raise ValueError(f"The value for the {tool_name} key must be a dictionary.")

        if "class" not in tool_info:
            raise ValueError(
                "Missing required key: 'class'.\n"
                "Each tool configuration must include a 'class' key specifying the fully qualified class name.\n"
                "Example: 'class': 'langchain_community.tools.bing_search.BingSearchResults'."
            )

        # Instance can be a BaseTool or a BaseToolkit
        instance: Union[BaseTool, BaseToolkit] = None
        # The combined arguments of user_args and class or method args
        final_args: Dict[str, Any] = None

        # If a method is specified (e.g., "from_github_api_wrapper"), use it instead of constructor
        method_info: Dict[str, Any] = tool_info.get("method", empty)
        if method_info:
            method_name: str = method_info.get("name")
            if not method_name:
                raise ValueError(
                    "Please specify the class method to load the toolkit."
                    "In general, the mehod is in the form of 'from_<tool_name>_api_wrapper'."
                )

            # Recursively resolve arguments (including wrapper dependencies)
            # Return arguments of class method
            method_args: Dict[str, Any] = self._resolve_args(method_info.get("args", empty))

            # Merge user args where user_args get the priority
            final_args = self.overlayer.overlay(method_args, user_args) if user_args else method_args

            # Resolve the toolkit class
            toolkit_class: Type[BaseToolkit] = self._resolve_class(tool_info.get("class"))

            # Call the class method dynamically
            if not hasattr(toolkit_class, method_name):
                raise ValueError(f"Method '{method_name}' not found in '{toolkit_class.__name__}'.")

            method = getattr(toolkit_class, method_name)
            # Check for arguments validity and call the method
            self._check_invalid_args(method, final_args)
            instance = method(**final_args)
        else:
            # Regular instantiation case for BaseTool or BaseToolkit that use constructor

            # Recursively resolve arguments (including wrapper dependencies)
            resolved_args: Dict[str, Any] = self._resolve_args(tool_info.get("args", empty))

            # Merge with user arguments where user_args get the priority
            final_args = self.overlayer.overlay(resolved_args, user_args) if user_args else resolved_args

            # Instantiate the main tool or toolkit class
            tool_class: Type[Any] = self._resolve_class(tool_info.get("class"))
            self._check_invalid_args(tool_class, final_args)
            instance = tool_class(**final_args)

        # If the instantiated class has "get_tools()", assume it's a toolkit and return a list of tools
        if hasattr(instance, "get_tools") and callable(instance.get_tools):
            return instance.get_tools()

        return instance

    def _resolve_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursive resolves arguments when there is a wrapper class as an argument,
        otherwise return args as a dictionary.

        :param args: The arguments to resolve.
        :return: A dictionary of resolved arguments.
        """
        empty: Dict[str, Any] = {}

        resolved_args: Dict[str, Any] = {}
        for key, value in args.items():
            if isinstance(value, dict) and "class" in value:
                # If the argument is a class definition, resolve and instantiate it
                nested_class: BaseModel = self._resolve_class(value.get("class"))
                nested_args: Dict[str, Any] = self._resolve_args(value.get("args", empty))
                self._check_invalid_args(nested_class, nested_args)
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

    def _check_invalid_args(self, method_class: Union[Type, MethodType], args: Dict[str, Any]):
        """
        Check for invalid arguments in class or method
        :param method_class: Class or method to check for the invalid arguments
        :param args: Arguments to check
        """
        class_args_set: Set[str] = set(signature(method_class).parameters.keys())
        args_set: Set[str] = set(args.keys())
        invalid_args: Set[str] = args_set - class_args_set

        if invalid_args:
            raise ValueError(
                f"Arguments {invalid_args} for '{method_class.__name__}' do not match any attributes "
                "of the class or any arguments of the method."
            )
