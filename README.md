# Neuro-San Data-Driven Agents

## Running client and server

### Prep

#### Install Python dependencies

From the top-level:

Set PYTHONPATH environment variable

    export PYTHONPATH=$(pwd)

Create and activate a new virtual environment:

    python3 -m venv venv
    . ./venv/bin/activate

Install packages specified in the following requirments files:

    pip install -r requirements.txt
    pip install -r requirements-build.txt


Most common:
If the dependency wheel files are available, install the wheel files for leaf-common
and leaf-server-common:

    pip install leaf-common.whl
    pip install leaf-server-common.whl

Less common:
If they are directly available via git, install the semi-private libraries
(like leaf-common and leaf-server-common):

    export LEAF_SOURCE_CREDENTIALS=<Your GitHub Personal Access Token>
    export LEAF_PRIVATE_SOURCE_CREDENTIALS=<Your GitHub Personal Access Token>
    pip install -r requirements-private.txt

#### Set necessary environment variables

In a terminal window, set at least these environment variables:

    export OPENAI_API_KEY="XXX_YOUR_OPENAI_API_KEY_HERE"

Any other API key environment variables for other LLM provider(s) also need to be set if you are using them.

### Direct Setup

From the top-level of this repo:

    python -m neuro_san.client.agent_cli --connection direct --agent hello_world

Type in this input to the chat client:

    I am travelling to a new planet and wish to send greetings to the orb.

What should return is something like:

    Hello, world.

... but you are dealing with LLMs. Your results will vary!

### Client/Server Setup

#### Server

In the same terminal window, be sure the environment variable(s) listed above
are set before proceeding.

Option 1: Run the service directly.  (Most useful for development)

    python -m neuro_san.service.agent_main_loop

Option 2: Build and run the docker container for the hosting agent service:

    ./neuro_san/deploy/build.sh ; ./neuro_san/deploy/run.sh

    You will need the leaf-common and leaf-server-common wheel files for this to work.

    These build.sh / Dockerfile / run.sh scripts are portable so they can be used with
    your own projects' registries and coded_tools work.


#### Client

In another terminal start the chat client:

    python -m neuro_san.client.agent_cli --connection service --agent hello_world


### Extra info about agent_cli.py

There is help to be had with --help.

By design, you cannot see all agents registered with the service from the client.

When the chat client is given a newline as input, that implies "send the message".
This isn't great when you are copy/pasting multi-line input.  For that there is a
--first_prompt_file argument where you can specify a file to send as the first
message.

You can send private data that does not go into the chat stream as a single escaped
string of a JSON dictionary. For example:
--sly_data "{ \"login\": \"<your login>\" }"


### Running Python unit/integration tests

To run a specifc unit test

- `pytest -v PathToPythonTestFile::TestClassName::TestMethodName`
- `pytest -v ./tests/client/test_client_response.py::TestClientResponse::test_beatles`

To run all unit tests

- `pytest -v ./tests`

To debug a specific unit test

- Import pytest in the test source file
  - `import pytest`
- Set a trace to stop the debugger on the next line
  - `pytest.set_trace()`
- Run pytest with '--pdb' flag
  - `pytest -v --pdb ./tests/client/test_client_response.py`

To run all integration tests

- `pytest -v -m "integration"`

## Creating a new agent network

### Agent example files

Look at the hocon files in ./neuro_san/registries for examples of specific agent networks.

The natural question to ask is: What is a hocon file?
The simplest answer is that you can think of a hocon file as a JSON file that allows for comments.

Here are some descriptions of the example hocon files provided in this repo.
To play with them, specify their stem as the argument for --agent on the agent_cli.py chat client.
In some order of complexity, they are:

*   hello_world

    This is the initial example used above and demonstrates
    a front-man agent talking to another agent downstream.

*   esp_decision_assistant

    This is Babak's original decision assistant.
    Very abstract, but also very powerful.
    A front man agent gathers information about a decision to make
    in ESP terms.  It then calls a prescriptor which in turn
    calls one or more predictors in order to help make the decision
    in an LLM-based ESP manner.

*   six_thinking_hats

    This is Hormoz's example of the six colored thinking hats
    approach to solving a problem.

*   intranet_agents

    This is Babak's "18-wheeler". A complex and abstract agent network
    that mimics a corporate help network, with divisional hierarchy
    encapsulated in one layer of agents, and specialized departments
    within those divisions attempt to answer basic corporate questions
    by means of delegation.

When coming up with new hocon files in that same directory, also add an entry for it
in the manifest.hocon file.

build.sh / run.sh the service like you did above to re-load the server,
and interact with it via the agent_cli.py chat client, making sure
you specify your agent correctly (per the hocon file stem).

### Manifest file

All agents used need to have an entry in a single manifest hocon file.
For the neuro-san repo, this is: neuro_san/registries/manifest.hocon.

When you create your own repo for your own agents, that will be different
and you will need to create your own manifest file.  To point the system
at your own manifest file, set a new environment variable:

    export AGENT_MANIFEST_FILE=<your_repo>/registries/manifest.hocon

# Infrastructure

The agent infrastructure is run as a gRPC service.
That gRPC service is implemented (client and server) using this interface:

https://github.com/leaf-ai/neuro-san/blob/main/neuro_san/session/agent_session.py

It has 2 main methods:

* function()

    This tells the client what the top-level agent will do for it.

* streaming_chat()

    This is the main entry point. Send some text and it starts a conversation
    with a "front man" agent.  If that guy needs more information it will ask
    you and you return your answer via another call to the chat() interface.
    ChatMessage Results from this method are streamed and when the conversation
    is over, the stream itself closes after the last message has been received.

    ChatMessages of various types will come back over the stream.
    Anything of type AI is the front-man answering you on behalf of the rest of
    its agent posse, so this is the kind you want to pay the most attention to.

* Other methods like chat(), logs(), and reset() are legacy

Implementations of the AgentSession interface:

* DirectAgentSession class.  Use this if you want to call neuro-san as a library
* ServiceAgentSession class. Use this if you want to call neuro-san as a client to a service

Note that agent_cli uses both of these.  You can look at the source code there for examples.

There is also an AsyncServiceAgentSession implementation available

# Advanced concepts

## Coded Tools

Most of the examples provided here show how no-code agents are put together,
but neuro-san agent networks support the notion of coded tools for
low-code solutions.

These are most often used when an agent needs to call out to a specific
web service, but they can be any kind of Python code as long it
derives from the CodedTool interface defined in neuro_san/interfaces/coded_tool.py.
See the class and method comments there for more information.

When you develop your own coded tools, there is another environment variable
that comes into play:

    export AGENT_TOOL_PATH=<your_repo>/coded_tools

Beneath this, classes are dynamically resolved based on their agent name.
That is, if you added a new coded tool to your agent, its file path would
look like this:

    <your_repo>/coded_tools/<your_agent_name>/<your_coded_tool>.py

# Creating Clients

## Python Clients
If you are using Python to create your client, then you are in luck!
The command line client at neuro_san/client/agent_cli.py is a decent example
of how to construct a chat client in Python.

A little deeper under the hood, that agent_cli client uses these classes under neuro_san/session
to connect to a server:

Synchronous connection:
* GrpcServiceAgentSession
* HttpServiceAgentSession

It also uses the DirectAgentSession to call the neuro-san infrastructure as a library.
There are async version of all of the above as well.

## Other clients.

A neuro-san server uses gRPC under the hood. You can check out the protobufs definition of the
API under neuro_san/api/grpc.  The place to start is agent.proto for the service definitions.
The next most important file there is chat.proto for the chat message definitions.

While gRPC data transimission is more compact, most clients will likely want to use the http
interface for ease of use in terms of web-apps and dev-ops administration.

### Using curl to interact with a neuro-san server

In one window start up a neuro-san server:

    python -m neuro_san.service.agent_main_loop

In another window, you can interact with this server via curl.

#### Getting an agent's prompt

Specific neuro-san agents are accessed by including the agent name in the route.
To get the hello_world agent's prompt, we do a GET to the function url for the agent:

curl --request GET --url localhost:8080/api/v1/hello_world/function

returns:

{
    "function": {
        "description": "\nI can help you to make a terse anouncement.\nTell me what your target audience is, and what sentiment you would like to relate.\n"
    }
}

The description field of the function structure is a user-displayable prompt.

#### Communicating with an agent

##### Initial User Request

Using the same principle of specifying the agent name in a route, we can use the hello_world
url to initiate a conversation with an agent with a POST:

curl --request POST --url localhost:8080/api/v1/hello_world/streaming_chat --data @- << EOF
{
    "user_message": {
        "text": "I approach a new planet and wish to send greetings to the orb."
    },
    "chat_filter": {
        "chat_filter_type": "MINIMAL"
    }
}
EOF

This will result in a stream of 2 chat messages structures coming back until the processing of the request is finished:

Message 1:

{
    "request": <blah blah>,
    "response": {
        "type": "AI",
        "text": "The announcement \"Hello, world!\" is an apt and concise greeting for the new planet.",
        "origin": [
            {
                "tool": "announcer",
                "instantiation_index": 1
            }
        ]
    }
}

This first response is telling you:
    * The message from the hello_world agent network was a typical "AI"-typed message.
      AI messages are the results coming from an LLM.
    * The "text" of what came back in the AI message - "Hello, world!" with typical extra LLM elaborating text. 
    * The "origin" is of length 1, which tells you that it came from the network's front-man agent,
      whose job it was to assemble an answer from all the other agents in the network.
    * That front-man's internal name is "announcer" (look it up in hello_world.hocon)
    * The "instantiation_index" tells us there was only one of those announcers.

For a single-shot conversation, this is all you really need to report back to your user.
But if you want to continue the conversation, you will need to pay attention to the second message.

Message 2:

Now what comes back as the 2nd message is actually fairly large, but for purposes of this conversation,
the details of the content are not as important.

{
    "request": <blah blah>,
    "response": {
        "type": "AGENT_FRAMEWORK",
        "chat_context": {
            <blah blah>
        }
    }
}

This tells you:
    * The message from the hello_world agent network was an "AGENT_FRAMEWORK" message.
      These kinds of messages come from neuro-san itself, not from any particular agent
      within the network.
    * The chat_context that is returned is a structure that helps you continue the conversation.
      For the most part, you can think of this as semi-opaque chat history data.

##### Continuing the conversation

In order to continue the conversation, you simply take the value of the last AGENT_FRAMEWORK message's
chat_context and add that to your next streaming_chat request:

curl --request POST --url localhost:8080/api/v1/hello_world/streaming_chat --data @- << EOF
{
    "user_message": {
        "text": "I approach a new planet and wish to send greetings to the orb."
    },
    "chat_filter": {
        "chat_filter_type": "MINIMAL"
    },
    "chat_context": {
        <blah blah>
    }
}
EOF

... and back comes the next result for your conversation
