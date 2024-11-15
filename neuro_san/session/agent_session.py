
from typing import Any
from typing import Dict


class AgentSession:
    """
    Interface for the initiation and continuity of a single Agent session.
    """

    # Default port for the Agent Service
    # This port number will also be mentioned in its Dockerfile
    DEFAULT_PORT: int = 30011

    # Some constants
    FOUND: int = 1
    NOT_FOUND: int = 2
    CREATED: int = 3

    def function(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the FunctionRequest
                    protobufs structure. Has the following keys:
                        <None>
        :return: A dictionary version of the FunctionResponse
                    protobufs structure. Has the following keys:
                "function" - the dictionary description of the function
                "status" - status for finding the function.
        """
        raise NotImplementedError

    def chat(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the ChatRequest
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
                              Upon first contact this can be blank.
            "user_input"    - A string representing the user input to the chat stream

        :return: A dictionary version of the ChatResponse
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
                              This will always be filled upon response.
            "status"        - An int representing the chat session's status. Can be one of:
                              FOUND     - The given session_id is alive and well
                                          on this service instance and the user_input
                                          has been registered in the chat stream.
                              NOT_FOUND - Returned if the service instance does not find
                                          the session_id given in the request.
                                          For continuing chat streams, this could imply
                                          a series of client-side retries as multiple
                                          service instances will not keep track of the same
                                          chat sessions.
                              CREATED   - Returned when no session_id was given (initiation
                                          of new chat by client) and a new chat session is created.

            Note that responses to the chat input are asynchronous and come by polling the
            logs() method below.
        """
        raise NotImplementedError

    def logs(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the LogsRequest
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
                              When calling logs(), this cannot be blank.

        :return: A dictionary version of the LogsResponse
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat sessions's resources.
            "status"        - An int representing the chat session's status. Can be one of:
                              FOUND     - The given session_id is alive and well
                                          on this service instance.
                                          Other keys below will be filled in.
                              NOT_FOUND - Returned if the service instance does not find
                                          the session_id given in the request.
                                          For continuing chat streams, this could imply
                                          a series of client-side retries as multiple
                                          service instances will not keep track of the same
                                          chat sessions.
                              CREATED   - While valid in other situations, this method will
                                          never return this value.
            "chat_response" - A single string representing the most recent chat response.
            "logs"          - A list of strings representing the "thinking" logs thus far.

            Worth noting that this particular method does not need to be asynchronous.
        """
        raise NotImplementedError

    def reset(self, request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        :param request_dict: A dictionary version of the ResetRequest
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat sessions's resources.
                              When calling reset(), this cannot be blank.
        :return: A dictionary version of the ResetResponse
                    protobufs structure. Has the following keys:
            "session_id"  - A string UUID identifying the root ownership of the
                              chat session's resources.
            "status"        - An int representing the chat session's status. Can be one of:
                              FOUND     - The given session_id is alive and well
                                          and has been reset. No retry needed.
                              NOT_FOUND - Returned if the service instance does not find
                                          the session_id given in the request.
                                          For continuing chat streams, this could imply
                                          a series of client-side retries as multiple
                                          service instances will not keep track of the same
                                          chat sessions.
                              CREATED   - While valid in other situations, this method will
                                          never return this value.
        """
        raise NotImplementedError
