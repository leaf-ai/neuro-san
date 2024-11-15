# Data-Driven Agents

## Running client and server

### Prep

From the top-level:

In a new virtual environment:

    pip install -r requirements.txt
    pip install -r requirements-build.txt

Generate the gRPC code:

    ./backend/grpc/do_generate.sh
    ./backend/grpc/do_mdserver_generate.sh

### Direct Setup

In a terminal window, set at least OPENAI_API_KEY to a valid access key for ChatGPT access.
(Any other API key environment variables for other LLMs also need to be set if you are using them.)

    export OPENAI_API_KEY="XXX"

From the top-level:

    python ./tests/backend/agents/agent_cli.py --connection direct --agent hello_world

Type in this input to the chat client:

    I am travelling to a new planet and wish to send greetings to the orb.

What should return is something like:

    Hello, world.

### Client/Server Setup

#### Server

In one terminal window, set at least OPENAI_API_KEY to a valid access key for ChatGPT access.
(Any other API key environment variables for other LLMs also need to be set if you are using them.)

    export OPENAI_API_KEY="XXX"

Build and run the docker container for the hosting agent service:

    ./backend/agents/service/build.sh ; ./backend/agents/service/run.sh

#### Client

In another terminal start the chat client:

    python ./tests/backend/agents/agent_cli.py --connection service --agent hello_world


### Extra info about agent_cli.py

There is help to be had with --help.

By design, you cannot see all agents registered with the service.

When the chat client is given a newline as input, that implies "send the message".
This isn't great when you are copy/pasting multi-line input.  For that there is a
--first_prompt_file argument where you can specify a file to send as the first
message.

You can send private data that does not go into the chat stream as a single escaped
string of a JSON dictionary. For example:
--sly_data "{ \"login\": \"<your login>\" }"

## Creating a new agent network

Look at the example hocon files in ./backend/agents/registries

Here are some descriptions of the example hocon files.
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

*   opportunity_finder_pipeline

    A practical example used by the NeuroAI system.
    It demostrates an agent pipeline taking natural language input,
    which extracts information out of that to compile
    a complex JSON structure.  Along the way it calls
    several coded-tools which each call web services to get
    pieces of the job done.

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

# Infrastructure

The agent infrastructure is run as a gRPC service.
That gRPC service is implemented (client and server) using this interface:

https://github.com/neuro-san/blob/main/neuro_san/session/agent_session.py

It has 4 methods:

* prompt()

    This tells the client what the top-level agent will do for it.

* chat()

    This is the main entry point. Send some text and it starts a conversation
    with a "front man" agent.  If that guy needs more information it will ask
    you and you return your answer via another call to the chat() interface.
    It's worth noting that these chat sessions are likely to take longer
    than the typical socket timeout (30-45secs) so the service stores a session
    id for each chat.

* logs()

    This shows all the agent chat history so far for a given session id.
    Think of this as seeing all of the internal "thinking" that the agents
    are doing talking to each other

* reset()

    This basically says restart this chat from nothing as if there were no
    chat history or context


# Adding agents that are UI-visible

1. Be sure your agent is added to the ./backend/agents/registries/manifest.hocon
2. Add an enum entry in proto/metadata.proto to the AgentType enum
    Be sure it is spelled the same as your agent hocon file's stem, but in all upper case.
    Note that while more agents might be listed in the manifest.hocon, it is this enum that controls
    what is available to the UI.
3. In backend/pmdserver/service/forwarded_agent_session.py, add 2 separate entries to the ENUM_TO_AGENT map:
    a. One will be a mapping from the AGENT_TYPE.<enum_value> integer to the all-smalls agent name string
    b. One will be a mapping from the all-caps enum name string to the all-smalls agent name string
4. Get with a UI guy to allow the UI to access the new agent

Your agent should now be available for public consumption.
