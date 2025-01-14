# Neuro-San Data-Driven Agents

## Running client and server

### Prep

#### Install Python dependencies

From the top-level:

In a new virtual environment:

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

