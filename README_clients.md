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
```
{
    "function": {
        "description": "\nI can help you to make a terse anouncement.\nTell me what your target audience is, and what sentiment you would like to relate.\n"
    }
}
```

The description field of the function structure is a user-displayable prompt.

#### Communicating with an agent

##### Initial User Request

Using the same principle of specifying the agent name in a route, we can use the hello_world
url to initiate a conversation with an agent with a POST:

```
curl --request POST --url localhost:8080/api/v1/hello_world/streaming_chat --data '{
    "user_message": {
        "text": "I approach a new planet and wish to send greetings to the orb."
    },
    "chat_filter": {
        "chat_filter_type": "MINIMAL"
    }
}'
```

This will result in a stream of 2 chat messages structures coming back until the processing of the request is finished:
```
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
```
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
```
{
    "request": <blah blah>,
    "response": {
        "type": "AGENT_FRAMEWORK",
        "chat_context": {
            <blah blah>
        }
    }
}
```
This tells you:
    * The message from the hello_world agent network was an "AGENT_FRAMEWORK" message.
      These kinds of messages come from neuro-san itself, not from any particular agent
      within the network.
    * The chat_context that is returned is a structure that helps you continue the conversation.
      For the most part, you can think of this as semi-opaque chat history data.

##### Continuing the conversation

In order to continue the conversation, you simply take the value of the last AGENT_FRAMEWORK message's
chat_context and add that to your next streaming_chat request:

```
curl --request POST --url localhost:8080/api/v1/hello_world/streaming_chat --data '{
    "user_message": {
        "text": "I approach a new planet and wish to send greetings to the orb."
    },
    "chat_filter": {
        "chat_filter_type": "MINIMAL"
    },
    "chat_context": {
        <blah blah>
    }
}'
```
... and back comes the next result for your conversation
