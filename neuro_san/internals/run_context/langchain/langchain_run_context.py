
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
from typing import Tuple
from typing import Union

import json
import traceback
import uuid

from logging import Logger
from logging import getLogger

from openai import APIError

from pydantic_core import ValidationError

from langchain.agents import Agent
from langchain.agents import AgentExecutor
from langchain.agents.conversational.base import ConversationalAgent
from langchain.agents.tool_calling_agent.base import create_tool_calling_agent
from langchain.base_language import BaseLanguageModel
from langchain.callbacks.tracers.logging import LoggingCallbackHandler
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.base import BaseMessage
from langchain_core.messages.human import HumanMessage
from langchain_core.messages.system import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool

from neuro_san.internals.errors.error_detector import ErrorDetector
from neuro_san.internals.interfaces.async_agent_session_factory import AsyncAgentSessionFactory
from neuro_san.internals.interfaces.invocation_context import InvocationContext
from neuro_san.internals.journals.journal import Journal
from neuro_san.internals.journals.originating_journal import OriginatingJournal
from neuro_san.internals.messages.origination import Origination
from neuro_san.internals.messages.agent_message import AgentMessage
from neuro_san.internals.messages.agent_tool_result_message import AgentToolResultMessage
from neuro_san.internals.messages.message_utils import convert_to_base_message
from neuro_san.internals.messages.message_utils import convert_to_message_tuple
from neuro_san.internals.run_context.interfaces.agent_tool_factory import AgentToolFactory
from neuro_san.internals.run_context.interfaces.run import Run
from neuro_san.internals.run_context.interfaces.run_context import RunContext
from neuro_san.internals.run_context.interfaces.tool_caller import ToolCaller
from neuro_san.internals.run_context.langchain.journaling_callback_handler import JournalingCallbackHandler
from neuro_san.internals.run_context.langchain.journaling_tools_agent_output_parser \
    import JournalingToolsAgentOutputParser
from neuro_san.internals.run_context.langchain.langchain_run import LangChainRun
from neuro_san.internals.run_context.langchain.langchain_openai_function_tool \
    import LangChainOpenAIFunctionTool
from neuro_san.internals.run_context.langchain.langchain_token_counter import LangChainTokenCounter
from neuro_san.internals.run_context.langchain.default_llm_factory import DefaultLlmFactory
from neuro_san.internals.run_context.utils.external_agent_parsing import ExternalAgentParsing
from neuro_san.internals.run_context.utils.external_tool_adapter import ExternalToolAdapter


MINUTES: float = 60.0


# pylint: disable=too-many-instance-attributes
class LangChainRunContext(RunContext):
    """
    LangChain implementation on RunContext interface supporting high-level LLM usage
    This ends up being useful:
        https://python.langchain.com/docs/modules/tools/tools_as_openai_functions/
    Note that "tools" can be just a list of OpenAI functions JSON.
    """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(self, llm_config: Dict[str, Any],
                 parent_run_context: RunContext,
                 tool_caller: ToolCaller,
                 invocation_context: InvocationContext,
                 chat_context: Dict[str, Any]):
        """
        Constructor

        :param llm_config: The default llm_config to use as an overlay
                            for the tool-specific llm_config
        :param parent_run_context: The parent RunContext that is calling this one. Can be None.
        :param tool_caller: The tool caller to use
        :param invocation_context: The context policy container that pertains to the invocation
                    of the agent.
        :param chat_context: A ChatContext dictionary that contains all the state necessary
                to carry on a previous conversation, possibly from a different server.
        """
        # This block contains top candidates for state storage that needs to be
        # retained when session_ids go away.
        self.chat_history: List[BaseMessage] = []
        self.journal: OriginatingJournal = None
        self.llm: BaseLanguageModel = None
        self.agent: Agent = None

        # This might get modified in create_resources() (for now)
        self.llm_config: Dict[str, Any] = llm_config
        self.run_id_base: str = str(uuid.uuid4())

        self.tools: List[BaseTool] = []
        self.error_detector: ErrorDetector = None
        self.recent_human_message: HumanMessage = None
        self.tool_caller: ToolCaller = tool_caller
        self.invocation_context: InvocationContext = invocation_context
        self.chat_context: Dict[str, Any] = chat_context
        self.origin: List[Dict[str, Any]] = []
        # Default logger
        self.logger: Logger = getLogger(self.__class__.__name__)

        parent_origin: List[Dict[str, Any]] = []
        if parent_run_context is not None:

            # Get other stuff from parent if not specified
            if self.invocation_context is None:
                self.invocation_context = parent_run_context.get_invocation_context()
            if self.chat_context is None:
                self.chat_context = parent_run_context.get_chat_context()
            parent_origin = parent_run_context.get_origin()

            # Initialize the origin.
            agent_name: str = tool_caller.get_name()
            origination: Origination = self.invocation_context.get_origination()
            self.origin = origination.add_spec_name_to_origin(parent_origin, agent_name)

        self.update_from_chat_context(self.chat_context)

        # Set up so local logging gives origin info.
        if self.origin is not None and len(self.origin) > 0:
            full_name: str = Origination.get_full_name_from_origin(self.origin)
            self.logger = getLogger(full_name)

        if self.invocation_context is not None:
            base_journal: Journal = self.invocation_context.get_journal()
            self.journal = OriginatingJournal(base_journal, self.origin, self.chat_history)

    async def create_resources(self, assistant_name: str,
                               instructions: str,
                               assignments: str,
                               tool_names: List[str] = None):
        """
        Creates resources for later use within the RunContext instance.
        Results are stored as a member in this instance for future use.

        Note that even though this method is labeled as async, we don't
        really do any async method calls in here for this implementation.

        :param assistant_name: String name of the assistant
        :param instructions: string instructions that are used
                    to create the assistant/agent
        :param assignments: string assignments of function parameters that are used as input
        :param tool_names: The list of registered tool names to use.
                    Default is None implying no tool is to be called.
        """
        # DEF - Remove the arg if possible
        _ = assistant_name

        # Create the list of callbacks to pass to the LLM ChatModel
        callbacks: List[BaseCallbackHandler] = [
            JournalingCallbackHandler(self.journal)
        ]
        full_name: str = Origination.get_full_name_from_origin(self.origin)

        # Consult the agent spec for level of verbosity as it pertains to callbacks.
        agent_spec: Dict[str, Any] = self.tool_caller.get_agent_tool_spec()
        verbose: Union[bool, str] = agent_spec.get("verbose", False)
        if isinstance(verbose, str) and verbose.lower() in ("extra", "logging"):
            # This particular class adds a *lot* of very detailed messages
            # to the logs.  Add this because some people are interested in it.
            callbacks.append(LoggingCallbackHandler(self.logger))

        # Create the model we will use.
        llm_factory = DefaultLlmFactory()
        llm_factory.load()
        self.llm = llm_factory.create_llm(self.llm_config, callbacks=callbacks)

        # Now that we have a name, we can create an ErrorDetector for the output.
        self.error_detector = ErrorDetector(full_name,
                                            error_formatter_name=agent_spec.get("error_formatter"),
                                            system_error_fragments=["Agent stopped"],
                                            agent_error_fragments=agent_spec.get("error_fragments"))

        if tool_names is not None:
            for tool_name in tool_names:
                tool: BaseTool = await self._create_base_tool(tool_name)
                if tool is not None:
                    self.tools.append(tool)

        prompt_template: ChatPromptTemplate = await self._create_prompt_template(instructions, assignments)

        if len(self.tools) > 0:
            self.agent = create_tool_calling_agent(self.llm, self.tools, prompt_template)

            # The above call creates a chain in this order:
            #   first:  RunnablePassthrough
            #   middle: prompt
            #           llm_with_tools
            #   last:   ToolsAgentOutputParser
            #
            # ... we need to mess with that a bit

            # Replace the output parser from the call above.
            # Per empirical experience, this is "last".
            self.agent.last = JournalingToolsAgentOutputParser(self.journal)
        else:
            self.agent = ConversationalAgent.from_llm_and_tools(self.llm, self.tools,
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
            if not ExternalAgentParsing.is_external_agent(name):
                return None

            # Use the ExternalToolAdapter to get the function specification
            # from the service call to the external agent.
            # We should be able to use the same BaseTool for langchain integration
            # purposes as we do for any other tool, though.
            # Optimization:
            #   It's possible we might want to cache these results somehow to minimize
            #   network calls.
            session_factory: AsyncAgentSessionFactory = self.invocation_context.get_async_session_factory()
            adapter = ExternalToolAdapter(session_factory, name)
            try:
                function_json = await adapter.get_function_json(self.invocation_context)
            except ValueError:
                # Could not reach the server for the external agent, so tell about it
                message: str = f"Agent/tool {name} was unreachable. Not including it as a tool."
                agent_message = AgentMessage(content=message)
                await self.journal.write_message(agent_message)
                self.logger.info(message)
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

    async def _create_prompt_template(self, instructions: str, assignments: str) -> ChatPromptTemplate:
        """
        Creates a ChatPromptTemplate given the generic instructions
        """
        # Assemble the prompt message list
        message_list: List[Tuple[str, str]] = []

        if len(self.chat_history) == 0:
            # We have not had any chat history just yet, so build it from scratch
            # Add to our own chat history which is updated in write_message()
            system_message = SystemMessage(instructions)
            await self.journal.write_message(system_message)
            message_list.append(("system", instructions))

            # If we have assignments, add them
            if assignments is not None and len(assignments) > 0:
                system_message = SystemMessage(assignments)
                await self.journal.write_message(system_message)
                message_list.append(("system", assignments))
        else:
            # Build the prompt template from previous chat history
            # Note that since all of these are from the chat history,
            # we can consider them already reported so they do not
            # need to get written to the journal.
            for index, base_message in enumerate(self.chat_history):

                message_tuple: Tuple[str, Any] = None

                if index == 0:
                    # Always use the most current instructions
                    message_tuple = ("system", instructions)
                else:
                    message_tuple = convert_to_message_tuple(base_message)

                if message_tuple is not None:
                    message_list.append(message_tuple)

        # Fill out the rest of the prompt per the docs for create_tooling_agent()
        # Note we are not write_message()-ing the chat history because that is redundant
        # Unclear if we should somehow/someplace write_message() the agent_scratchpad at all.
        message_list.extend([
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

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
        try:
            self.recent_human_message = HumanMessage(user_message)
        except ValidationError as exception:
            full_name: str = Origination.get_full_name_from_origin(self.origin)
            message = f"ValidationError in {full_name} with message: {user_message}"
            raise ValueError(message) from exception

        # Create a run to return
        run = LangChainRun(self.run_id_base, self.chat_history)
        return run

    # pylint: disable=too-many-locals
    async def wait_on_run(self, run: Run, journal: Journal = None) -> Run:
        """
        Loops on the given run's status for model invokation.

        This truly is an asynchronous method.

        :param run: The run to wait on
        :param journal: The Journal which captures the "thinking" messages.
        :return: An potentially updated run
        """

        # Create an agent executor and invoke it with the most recent human message
        # as input.
        agent_spec: Dict[str, Any] = self.tool_caller.get_agent_tool_spec()

        verbose: Union[bool, str] = agent_spec.get("verbose", False)
        if isinstance(verbose, str):
            verbose = bool(verbose.lower() in ("true", "extra", "logging"))

        max_execution_seconds: float = agent_spec.get("max_execution_seconds",
                                                      2.0 * MINUTES)
        max_iterations: int = agent_spec.get("max_iterations", 20)
        agent_executor = AgentExecutor(agent=self.agent,
                                       tools=self.tools,
                                       max_execution_time=max_execution_seconds,
                                       max_iterations=max_iterations,
                                       verbose=verbose)

        run: Run = LangChainRun(self.run_id_base, self.chat_history)

        # Chat history is updated in write_message
        await self.journal.write_message(self.recent_human_message)

        inputs = {
            "chat_history": self.chat_history,
            "input": self.recent_human_message
        }
        invoke_config = {
            "configurable": {
                "session_id": run.get_id()
            }
        }

        # Attempt to count tokens/costs while invoking the agent.
        token_counter = LangChainTokenCounter(self)
        await token_counter.count_tokens(self.ainvoke(agent_executor, inputs, invoke_config))

        return run

    async def ainvoke(self, agent_executor: AgentExecutor, inputs: Dict[str, Any], invoke_config: Dict[str, Any]):
        """
        Set the agent in motion

        :param agent_executor: The AgentExecutor to invoke
        :param inputs: The inputs to the agent_executor
        :param invoke_config: The invoke_config to send to the agent_executor
        """
        return_dict: Dict[str, Any] = None
        retries: int = 3
        exception: Exception = None
        backtrace: str = None
        while return_dict is None and retries > 0:
            try:
                return_dict: Dict[str, Any] = await agent_executor.ainvoke(inputs, invoke_config)
            except APIError as api_error:
                self.logger.warning("retrying from openai.APIError")
                retries = retries - 1
                exception = api_error
                backtrace = traceback.format_exc()
            except KeyError as key_error:
                self.logger.warning("retrying from KeyError")
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
                    self.logger.warning("retrying from ValueError")
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

        # Chat history is updated in write_message
        await self.journal.write_message(return_message)

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
                if tool_messages is not None:
                    for tool_message in tool_messages:
                        # Chat history is updated in write_message()
                        await self.journal.write_message(tool_message)

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
            # Dunno what to do with None tool output
            return None
        if isinstance(tool_chat_list_string, tuple):
            # Sometimes output comes back as a tuple.
            # The output we want is the first element of the tuple.
            tool_chat_list_string = tool_chat_list_string[0]
        if not isinstance(tool_chat_list_string, str):
            self.logger.warning("Dunno what to do with %s tool output %s",
                                str(tool_chat_list_string.__class__.__name__),
                                str(tool_chat_list_string))
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
            self.logger.error("Exception: %s parsing %s", str(exception), str(tool_chat_list_string))
            raise exception

        # The tool_output seems to contain the entire chat history of
        # the call to the tool. For now just take the last one as the answer.
        tool_result_dict = tool_chat_list[-1]

        # Turn that guy into a BaseMessage
        # You might expect that this should be a ToolMessage, but making that
        # kind of conversion at this point runs into problems with OpenAI models
        # that process them.  So, to make things continue to work, report the
        # content as an AI message - as if the bot came up with the answer itself.
        tool_message = AgentToolResultMessage(content=tool_result_dict.get("content"),
                                              tool_result_origin=tool_output.get("origin"))

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
        self.llm = None
        self.journal = None

    def get_agent_tool_spec(self) -> Dict[str, Any]:
        """
        :return: the dictionary describing the data-driven agent
        """
        if self.tool_caller is None:
            return None

        return self.tool_caller.get_agent_tool_spec()

    def get_invocation_context(self) -> InvocationContext:
        """
        :return: The InvocationContext policy container that pertains to the invocation
                    of the agent.
        """
        return self.invocation_context

    def get_chat_context(self) -> Dict[str, Any]:
        """
        :return: A ChatContext dictionary that contains all the state necessary
                to carry on a previous conversation, possibly from a different server.
                Can be None when a new conversation has been started.
        """
        return self.chat_context

    def get_origin(self) -> List[Dict[str, Any]]:
        """
        :return: A List of origin dictionaries indicating the origin of the run.
                The origin can be considered a path to the original call to the front-man.
                Origin dictionaries themselves each have the following keys:
                    "tool"                  The string name of the tool in the spec
                    "instantiation_index"   An integer indicating which incarnation
                                            of the tool is being dealt with.
        """
        return self.origin

    def update_invocation_context(self, invocation_context: InvocationContext):
        """
        Update internal state based on the InvocationContext instance passed in.
        :param invocation_context: The context policy container that pertains to the invocation
        """
        self.invocation_context = invocation_context

        base_journal: Journal = self.invocation_context.get_journal()
        self.journal = OriginatingJournal(base_journal, self.origin, self.chat_history)

    def update_from_chat_context(self, chat_context: Dict[str, Any]):
        """
        :param chat_context: A ChatContext dictionary that contains all the state necessary
                to carry on a previous conversation, possibly from a different server.
        """
        self.chat_context = chat_context

        if self.chat_context is None:
            return

        # See if our origin appears in the chat histories.
        # If so, get ours from there.
        empty: List[Any] = []
        chat_histories: List[Dict[str, Any]] = self.chat_context.get("chat_histories", empty)
        our_origin_str: str = Origination.get_full_name_from_origin(self.origin)
        for one_chat_history in chat_histories:

            # See if the origin matches our own
            test_origin: List[Dict[str, Any]] = one_chat_history.get("origin", empty)
            test_origin_str: str = Origination.get_full_name_from_origin(test_origin)
            if test_origin_str != our_origin_str:
                continue

            one_messages: List[Dict[str, Any]] = one_chat_history.get("messages", empty)
            if not one_messages:
                # Empty list - Nothing to convert. Use default empty list.
                break

            self.chat_history = []
            for chat_message in one_messages:
                base_message: BaseMessage = convert_to_base_message(chat_message)
                if base_message is not None:
                    self.chat_history.append(base_message)

            # Nothing left to search for
            break

    def get_journal(self) -> Journal:
        """
        :return: The Journal associated with the instance
        """
        return self.journal

    def get_llm(self) -> BaseLanguageModel:
        """
        :return: The LLM associated with the instance
        """
        return self.llm
