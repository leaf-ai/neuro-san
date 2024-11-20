
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
from typing import Any
from typing import Dict
from typing import List

import json
import uuid
import traceback

from openai import APIError

from langchain.agents import Agent
from langchain.agents import AgentExecutor
from langchain.agents.conversational.base import ConversationalAgent
from langchain.agents.tool_calling_agent.base import create_tool_calling_agent
from langchain.base_language import BaseLanguageModel
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.base import BaseMessage
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.system import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool

from neuro_san.errors.error_detector import ErrorDetector
from neuro_san.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.run_context.interfaces.run import Run
from neuro_san.run_context.interfaces.run_context import RunContext
from neuro_san.run_context.interfaces.tool_caller import ToolCaller
from neuro_san.run_context.langchain.langchain_run import LangChainRun
from neuro_san.run_context.langchain.langchain_openai_function_tool \
    import LangChainOpenAIFunctionTool
from neuro_san.run_context.langchain.llm_factory import LlmFactory
from neuro_san.run_context.utils.external_tool_adapter import ExternalToolAdapter
from neuro_san.utils.stream_to_logger import StreamToLogger


MINUTES: float = 60.0


# pylint: disable=too-many-instance-attributes
class LangChainRunContext(RunContext):
    """
    LangChain implementation on RunContext interface supporting high-level LLM usage
    This ends up being useful:
        https://python.langchain.com/docs/modules/tools/tools_as_openai_functions/
    Note that "tools" can be just a list of OpenAI functions JSON.
    """

    def __init__(self, llm_config: Dict[str, Any], tool_caller: ToolCaller):
        """
        Constructor

        :param llm_config: The default llm_config to use as an overlay
                            for the tool-specific llm_config
        :param tool_caller: The tool caller to use
        """

        # This might get modified in create_resources() (for now)
        self.llm_config: Dict[str, Any] = llm_config
        self.run_id_base: str = str(uuid.uuid4())

        self.tools: List[BaseTool] = []
        self.chat_history: List[BaseMessage] = []
        self.assistant_name: str = None
        self.agent: Agent = None
        self.error_detector: ErrorDetector = None
        self.recent_human_message: HumanMessage = None
        self.tool_caller: ToolCaller = tool_caller

    async def create_resources(self, assistant_name: str,
                               instructions: str,
                               tool_names: List[str] = None):
        """
        Creates resources for later use within the RunContext instance.
        Results are stored as a member in this instance for future use.

        Note that even though this method is labeled as async, we don't
        really do any async method calls in here for this implementation.

        :param assistant_name: String name of the assistant
        :param instructions: string instructions that are used
                    to create the assistant/agent
        :param tool_names: The list of registered tool names to use.
                    Default is None implying no tool is to be called.
        """
        # Create the model we will use.
        llm: BaseLanguageModel = LlmFactory.create_llm(self.llm_config)

        self.assistant_name = assistant_name

        agent_spec: Dict[str, Any] = self.tool_caller.get_agent_tool_spec()

        # Now that we have a name, we can create an ErrorDetector for the output.
        self.error_detector = ErrorDetector(assistant_name,
                                            error_formatter_name=agent_spec.get("error_formatter"),
                                            system_error_fragments=["Agent stopped"],
                                            agent_error_fragments=agent_spec.get("error_fragments"))

        if tool_names is not None:
            for tool_name in tool_names:
                tool: BaseTool = await self._create_base_tool(tool_name)
                if tool is not None:
                    self.tools.append(tool)

        prompt_template: ChatPromptTemplate = self._create_prompt_template(instructions)

        if len(self.tools) > 0:
            self.agent = create_tool_calling_agent(llm, self.tools, prompt_template)
        else:
            self.agent = ConversationalAgent.from_llm_and_tools(llm, self.tools,
                                                                prefix=instructions)

    async def _create_base_tool(self, name: str) -> BaseTool:
        """
        :param name: The name of the tool to create
        :return: The BaseTool associated with the name
        """

        factory: AgentToolFactory = self.tool_caller.get_factory()
        function_json: Dict[str, Any] = None

        # Check our own local factory. Most tools live in the neighborhood.
        agent_spec: Dict[str, Any] = factory.get_agent_tool_spec(name)
        if agent_spec is None:

            # See if the agent name given could reference an external agent.
            if not ExternalToolAdapter.is_external_agent(name):
                return None

            # Use the ExternalToolAdapter to get the function specification
            # from the service call to the external agent.
            # We should be able to use the same BaseTool for langchain integration
            # purposes as we do for any other tool, though.
            # Optimization:
            #   It's possible we might want to cache these results somehow to minimize
            #   network calls.
            adapter = ExternalToolAdapter(name)
            function_json = await adapter.get_function_json()
        else:
            function_json = agent_spec.get("function")

        if function_json is None:
            return None

        # In the case of an internal agent, the name passed in for lookup should be the
        # same as what is in the spec.
        if agent_spec is not None and name != agent_spec.get("name"):
            raise ValueError(f"Tool name mismatch.  name={name}  agent_spec.name={agent_spec.get('name')}")

        # In the case of external agents, if they report a name at all, they will
        # report something different that does not identify them as external.
        # Also, most internal agents do not have a name identifier on their functional
        # JSON, which is required.  Use the agent name we are using for look-up for that
        # regardless of intent.
        function_json["name"] = name

        function_tool: BaseTool = LangChainOpenAIFunctionTool.from_function_json(function_json,
                                                                                 self.tool_caller)
        return function_tool

    def _create_prompt_template(self, instructions: str) \
            -> ChatPromptTemplate:
        """
        Creates a ChatPromptTemplate given the generic instructions
        """
        # Add to our own chat history
        system_message = SystemMessage(instructions)
        self.chat_history.append(system_message)

        # Make a prompt per the docs for create_tooling_agent()
        message_list = [
            ("system", instructions),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
        prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(message_list)

        return prompt

    async def submit_message(self, user_message: str) -> Run:
        """
        Submits a message to the model used by this instance.

        Note that even though this method is labeled as async, we don't
        really do any async method calls in here for this implementation.

        :param user_message: The message to submit
        :return: The run which is processing the assistant's message
        """
        # Contruct a human message out of the text of the user message
        # Don't add this to the chat history yet.
        self.recent_human_message = HumanMessage(user_message)

        # Create a run to return
        run = LangChainRun(self.run_id_base, self.chat_history)
        return run

    # pylint: disable=too-many-locals
    async def wait_on_run(self, run: Run, logger: StreamToLogger = None) -> Run:
        """
        Loops on the given run's status for model invokation.

        This truly is an asynchronous method.

        :param run: The run to wait on
        :param logger: The StreamToLogger which captures the "thinking" messages.
        :return: An potentially updated run
        """

        # Create an agent executor and invoke it with the most recent human message
        # as input.
        agent_spec: Dict[str, Any] = self.tool_caller.get_agent_tool_spec()
        verbose = agent_spec.get("verbose", False)
        max_execution_seconds: float = agent_spec.get("max_execution_seconds",
                                                      2.0 * MINUTES)
        max_iterations: int = agent_spec.get("max_iterations", 20)
        agent_executor = AgentExecutor(agent=self.agent,
                                       tools=self.tools,
                                       max_execution_time=max_execution_seconds,
                                       max_iterations=max_iterations,
                                       verbose=verbose)

        run: Run = LangChainRun(self.run_id_base, self.chat_history)

        self.chat_history.append(self.recent_human_message)
        inputs = {
            "chat_history": self.chat_history,
            "input": self.recent_human_message
        }
        invoke_config = {
            "configurable": {
                "session_id": run.get_id()
            }
        }

        return_dict: Dict[str, Any] = None
        retries: int = 3
        exception: Exception = None
        backtrace: str = None
        while return_dict is None and retries > 0:
            try:
                return_dict: Dict[str, Any] = await agent_executor.ainvoke(inputs, invoke_config)
            except APIError as api_error:
                print("retrying from openai.APIError")
                retries = retries - 1
                exception = api_error
                backtrace = traceback.format_exc()
            except KeyError as key_error:
                print("retrying from KeyError")
                retries = retries - 1
                exception = key_error
                backtrace = traceback.format_exc()
            except ValueError as value_error:
                response = str(value_error)
                find_string = "An output parsing error occurred. " + \
                              "In order to pass this error back to the agent and have it try again, " + \
                              "pass `handle_parsing_errors=True` to the AgentExecutor. " + \
                              "This is the error: Could not parse LLM output: `"
                if response.startswith(find_string):
                    # Agent is returning good stuff, but langchain is erroring out over it.
                    # From: https://github.com/langchain-ai/langchain/issues/1358#issuecomment-1486132587
                    # Per thread consensus, this is hacky and there are better ways to go,
                    # but removes immediate impediments.
                    return_dict = {
                        "output": response.removeprefix(find_string).removesuffix("`")
                    }
                else:
                    print("retrying from ValueError")
                    retries = retries - 1
                    exception = value_error
                    backtrace = traceback.format_exc()

        output: str = None
        if return_dict is None and exception is not None:
            output = f"Agent stopped due to exception {exception}"
        else:
            # Other keys generally available at this point from return_dict are
            # "chat_history" and "input".
            output = return_dict.get("output", "")
            backtrace = None

        output = self.error_detector.handle_error(output, backtrace)

        return_message: BaseMessage = AIMessage(output)

        self.chat_history.append(return_message)
        return run

    async def get_response(self) -> List[Any]:
        """
        :return: The list of messages from the instance's thread.
        """
        # Not sure if this is the right thing, as this will be langchain-y stuff.
        return self.chat_history

    async def submit_tool_outputs(self, run: Run, tool_outputs: List[Any]) -> Run:
        """
        :param run: The run handling the execution of the assistant
        :param tool_outputs: The tool outputs to submit
        :return: A potentially updated run handle
        """
        if tool_outputs is not None and len(tool_outputs) > 0:
            for tool_output in tool_outputs:
                tool_messages: List[BaseMessage] = self.parse_tool_output(tool_output)
                if tool_messages is not None and len(tool_messages) > 0:
                    self.chat_history.extend(tool_messages)
        else:
            print("No tool_outputs")

        # Create a run to return
        run = LangChainRun(self.run_id_base, self.chat_history)

        return run

    def parse_tool_output(self, tool_output: Dict[str, Any]) -> List[BaseMessage]:
        """
        Parse a single tool_output dictionary for its results
        :return: A list of messages representing the output from the tool.
        """

        # Get a Message for each output and add to the chat history.
        # Assuming dictionary
        tool_chat_list_string = tool_output.get("output", None)
        if tool_chat_list_string is None:
            print("Dunno what to do with None tool output")
            return None
        if isinstance(tool_chat_list_string, tuple):
            # Sometimes output comes back as a tuple.
            # The output we want is the first element of the tuple.
            tool_chat_list_string = tool_chat_list_string[0]
        if not isinstance(tool_chat_list_string, str):
            print(f"Dunno what to do with {tool_chat_list_string.__class__.__name__} " +
                  f"tool output {tool_chat_list_string}")
            return None

        # Remove bracketing quotes from within the string
        while (tool_chat_list_string[0] == '"' and tool_chat_list_string[-1] == '"') or \
              (tool_chat_list_string[0] == "'" and tool_chat_list_string[-1] == "'"):
            tool_chat_list_string = tool_chat_list_string[1:-1]

        # Remove escaping
        tool_chat_list_string = tool_chat_list_string.replace('\\"', '"')
        # Put back some escaping of double quotes in messages that are not json.
        # We have to do this because gpt-4o seems to not like json braces in its
        # input, but now we have to deal with the consequences in the output.
        # See BranchTook._get_args_value_as_string().
        tool_chat_list_string = tool_chat_list_string.replace('\\"', '\\\\\"')

        # Decode the JSON in that string now.
        tool_chat_list: List[Dict[str, Any]] = None
        try:
            tool_chat_list = json.loads(tool_chat_list_string)
        except json.decoder.JSONDecodeError as exception:
            print(f"Exception: {exception} parsing {tool_chat_list_string}")
            raise exception

        # The tool_output seems to contain the entire chat history of
        # the call to the tool. For now just take the last one as the answer.
        tool_result_dict = tool_chat_list[-1]

        # Turn that guy into a BaseMessage
        tool_message = AIMessage(content=tool_result_dict.get("content"))

        return_messages: List[BaseMessage] = [tool_message]
        return return_messages

    async def delete_resources(self, parent_run_context: RunContext = None):
        """
        Cleans up the service-side resources associated with this instance
        :param parent_run_context: A parent RunContext perhaps the same instance,
                        but perhaps not.  Default is None
        """
        self.tools = []
        self.chat_history = []
        self.agent = None
        self.recent_human_message = None
