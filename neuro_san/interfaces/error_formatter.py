

# pylint: disable=too-few-public-methods
class ErrorFormatter:
    """
    Interface describing how error formatting can be called.

    Errors can come from various levels of the system - either as a result
    of the agents, or the agent framework itself.  In all cases, it benefits
    consumers of the agents' output to have consistent formatting of error
    messages regardless of source.
    """

    def format(self, agent_name: str, message: str, details: str = None) -> str:
        """
        Format an error message

        :param agent_name: A string describing the name of the agent experiencing
                the error.
        :param message: The specific message describing the error occurrence.
        :param details: An optional string describing further details of how/where the
                error occurred.  Think: traceback.
        :return: String encapsulation and/or filter of the error information
                presented in the arguments.
        """
        raise NotImplementedError
