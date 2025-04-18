# Neuro-San Data-Driven Agents

Neuro-San (System of Agent Networks) is a library for building data-driven multi-agent networks
which can be run as a library, or served up via an HTTP/gRPC server.

Motivation: People come with all their hopes and dreams to lay them at the altar
of a single LLM/agent expecting it to do the most complex tasks.  This often fails
because the scope is often too big for a single LLM to handle.  People expect the
equivalent of an adult PhD to be at their disposal, but what you really get is a high-school intern.

Solution: Allow these problems to be broken up into smaller pieces so that multiple LLM-enabled
agents can communicate with each other to solve a single problem.

Neuro-San agent networks can be entirely specified in a data-only
[HOCON](https://github.com/lightbend/config/blob/main/HOCON.md)
file format (think: JSON with comments, among other things), enabling subject matter experts
to be the authors of complex agent networks, not just programmers.

Neuro-San agent networks can also call CodedTools (langchain or our own interface) which do things
that LLMs can't on their own like: Query a web service, effectuate change via a web API, handle
private data correctly, do complex math operations, copy large bits of data without error.
While this aspect _does_ require programming skills, what the savvy gain with Neuro-San is a new way
to think about your problems that involves a weave between natural language tasks that LLMs are good at
and traditional computing tasks which deterministic Python code gives you.

Neuro-San also offers:

* channels for private data (aka sly_data) that should be kept out of LLM chat streams
* LLM-provider agnosticism and extensibiltiy of data-only-configured LLMs when new hotness arrives.
* agent-specific LLM specifications - use the right LLM for the cost/latency/context-window/data-privacy each agent needs.
* fallback LLM specifications for when your fave goes down.
* powerful debugging information for gaining insight into your mutli-agent systems.
* server-readiness at scale
* enabling of distributed agent webs that call each other to work together, wheverer they are hosted.
* security-by-default - you set what private data is to be shared downstream/upstream

## Running client and server

### Prep

#### Setup your virtual environment

##### Install Python dependencies

Set PYTHONPATH environment variable

    export PYTHONPATH=$(pwd)

Create and activate a new virtual environment:

    python3 -m venv venv
    . ./venv/bin/activate
    pip install neuro-san

OR from the neuro-san project top-level:
Install packages specified in the following requirements files:

    pip install -r requirements.txt

##### Set necessary environment variables

In a terminal window, set at least these environment variables:

    export OPENAI_API_KEY="XXX_YOUR_OPENAI_API_KEY_HERE"

Any other API key environment variables for other LLM provider(s) also need to be set if you are using them.

### Using as a library (Direct)

From the top-level of this repo:

    python -m neuro_san.client.agent_cli --agent hello_world

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

    These build.sh / Dockerfile / run.sh scripts are portable so they can be used with
    your own projects' registries and coded_tools work.

#### Client

In another terminal start the chat client:

    python -m neuro_san.client.agent_cli --http --agent hello_world

### Extra info about agent_cli.py

There is help to be had with --help.

By design, you cannot see all agents registered with the service from the client.

When the chat client is given a newline as input, that implies "send the message".
This isn't great when you are copy/pasting multi-line input.  For that there is a
--first_prompt_file argument where you can specify a file to send as the first
message.

You can send private data that does not go into the chat stream as a single escaped
string of a JSON dictionary. For example:
--sly_data "{ \"login\": \"your_login\" }"

## Running Python unit/integration tests

To run Python unit/integration tests, follow the instructions [here](https://github.com/leaf-ai/neuro-san/blob/main/README_tests.md)

## Creating a new agent network

### Agent example files

Look at the hocon files in ./neuro_san/registries for examples of specific agent networks.

The natural question to ask is: What is a hocon file?
The simplest answer is that you can think of a hocon file as a JSON file that allows for comments.

Here are some descriptions of the example hocon files provided in this repo.
To play with them, specify their stem as the argument for --agent on the agent_cli.py chat client.
In some order of complexity, they are:

* hello_world

    This is the initial example used above and demonstrates
    a front-man agent talking to another agent downstream.

* esp_decision_assistant

    This is Babak's original decision assistant.
    Very abstract, but also very powerful.
    A front man agent gathers information about a decision to make
    in ESP terms.  It then calls a prescriptor which in turn
    calls one or more predictors in order to help make the decision
    in an LLM-based ESP manner.

When coming up with new hocon files in that same directory, also add an entry for it
in the manifest.hocon file.

build.sh / run.sh the service like you did above to re-load the server,
and interact with it via the agent_cli.py chat client, making sure
you specify your agent correctly (per the hocon file stem).

### More agent example files

For more examples of agent networks, documentation and tutorials,
see the [neuro-san-demos repo.](https://github.com/leaf-ai/neuro-san-demos)

### Manifest file

All agents used need to have an entry in a single manifest hocon file.
For the neuro-san repo, this is: neuro_san/registries/manifest.hocon.

When you create your own repo for your own agents, that will be different
and you will need to create your own manifest file.  To point the system
at your own manifest file, set a new environment variable:

    export AGENT_MANIFEST_FILE=<your_repo>/registries/manifest.hocon

## Infrastructure

The agent infrastructure is run as a gRPC service.
That gRPC service is implemented (client and server) using the
[AgentSession](https://github.com/leaf-ai/neuro-san/blob/main/neuro_san/session/agent_session.py)
interface:

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

## Advanced concepts

### Coded Tools

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

## Creating Clients

To create clients, follow the instructions [here](https://github.com/leaf-ai/neuro-san/blob/main/README_clients.md)
