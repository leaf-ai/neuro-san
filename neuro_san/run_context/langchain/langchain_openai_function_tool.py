from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Optional
from typing import Type

import traceback

from langchain_core.tools import BaseTool

from neuro_san.run_context.interfaces.tool_caller import ToolCaller
from neuro_san.run_context.langchain.langchain_run import LangChainRun
from neuro_san.run_context.langchain.base_model_dictionary_converter \
    import BaseModelDictionaryConverter
from neuro_san.run_context.langchain.pydantic_argument_dictionary_converter \
    import PydanticArgumentDictionaryConverter


class LangChainOpenAIFunctionTool(BaseTool):
    """
    Class which represents an OpenAI Function as a langchain BaseTool.
    This is intended to partly be the reverse of format_tool_to_openai_function()

    This might seem antithetical as this just gets converted back
    to OpenAI function JSON in the langchain internals, but the idea
    is to have something at a higher level that plays well with
    the langchain Agent infrastructure.

    When this Tool's _arun() gets called, this allows the
    CallingTool (as ToolCaller) to set up other instances
    of LLM/Agent/AgentExecutor/RunContext to handle the tool call
    within that new context, but still within the async method chain.
    """

    # Declarations of member variables here satisfy Pydantic style,
    # which is a type validator that langchain is based on which
    # is able to use JSON schema definitions to validate fields.
    #
    # Also note that any of the function_json's parameters has to satisfy the
    # non-optional schema spec of this object. That is it needs:
    #       "name", "description" and "parameters" all as keys.

    # This group of member variables are required in OpenAI function definitions
    name: str
    description: str
    parameters: object

    # All the other "member" variables assigned below are typed as
    # "Optional" so that we can have this class function as we like.

    # This guy is required to satisfy langchain internals.
    # See comment near assignment in from_function_json() below.
    args_schema: Optional[Type[BaseTool]] = None

    # The actual schema we want to report
    function_json: Optional[Dict[str, Any]] = None

    tool_caller: Optional[ToolCaller] = None

    @staticmethod
    def from_function_json(function_json: Dict[str, Any],
                           tool_caller: ToolCaller) \
            -> LangChainOpenAIFunctionTool:
        """
        Creates an instance of this tool from prepared OpenAI Function JSON.
        """
        # This first call populates the name, description and parameters
        # members of this BaseTool implementation so that it satisfies
        # the actual description of the function_json that we expect to
        # be passed in which we expect to conform to an OpenAI function.
        # definition.
        tool = LangChainOpenAIFunctionTool(**function_json)

        # These next post-assignments satisfy the requirements of
        # convert_pydantic_to_openai_function() in that it wants to call
        # our schema() method to find out the function_json.
        use_function_json = function_json.get("parameters", function_json)
        tool.function_json = use_function_json

        # Langchain tools really prefer statically defined functions.
        # They are able to use some pretty fancy annotations and pydantic in order
        # to glean the function arguments and their types. We need more dynamism, though.
        #
        # The langchain_core BaseTool code for get_input_schema() expects there
        # to be an args_schema member which should be a pydantic BaseModel
        # for the objects that are passed as arguments.
        #
        # Create a pydantic BaseModel of the OpenAI function spec for the agent
        # to satisfy that langchain need.  It's kind of a shame because this is just
        # going to get converted back to an OpenAI function again later on in langchain
        #  agent-land.
        converter = BaseModelDictionaryConverter("parameters")
        tool.args_schema = converter.from_dict(use_function_json)

        tool.tool_caller = tool_caller

        return tool

    def _run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        raise NotImplementedError

    async def _arun(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Comment from lanchain's BaseTool:
        Use the tool.

        Add run_manager: Optional[AsyncCallbackManagerForToolRun] = None
        to child implementations to enable tracing,

        Commentary:

        This method actually does the work when the tool is called
        via the AgentExecutor framework.
        It uses the tool_caller member as a basis to call the
        make_tool_function_calls() method. That guy
        is going to go through all the impending calls to Tools
        and do them all in a separate AgentExecutor context.
        Since this method is a langchain "a" method, all of these
        calls to another llm/agent instance happen asynchronously.
        ("a" is for asynchronous).

        :return: The result of the tool in the form of the BaseMessage
                 that tells us the "answer" from the tool.
        """
        run: LangChainRun = None
        try:
            # Use the CallingTool/tool_caller to invoke
            # its other tools within the context of other llm/agent/tool
            # instances.

            # When passing along the arguments, convert any pydantic-created objects
            # into dictionaries before passing them along, no matter how deep in an
            # object/dictionary hierarchy they may be.
            converter = PydanticArgumentDictionaryConverter()
            kwargs = converter.to_dict(kwargs)

            decision_run = LangChainRun("tool_base", [""], self.name, kwargs)
            run = await self.tool_caller.make_tool_function_calls(decision_run)

        # pylint: disable=broad-exception-caught
        except Exception as exception:
            # Report the exception, but return None as value from function.
            # This actually allows LLMs to recognize that something is wrong
            # and verbally report on that.
            print(f"Tool._arun() got Exception: {exception}")
            print(traceback.format_exc())
            run = None

        if run is None:
            return None

        # Assume the last message in the Run's chat_history holds the answer.
        # This eventually gets integrated into the CallingTool/tool_caller
        # in its submit_tool_outputs() call for its RunContext.
        the_answer = run.get_chat_history()[-1]
        return the_answer
