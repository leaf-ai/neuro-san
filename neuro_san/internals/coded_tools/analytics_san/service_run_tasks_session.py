
from typing import Any
from typing import Dict
from typing import Tuple

from leaf_common.session.abstract_service_session import AbstractServiceSession
from leaf_common.time.timeout import Timeout

from neuro_san.api.grpc import tasks_service_pb2 as service_messages
from neuro_san.api.grpc import tasks_service_pb2_grpc as service_stub
from neuro_san.internals.coded_tools.analytics_san.task_status import TaskStatus


class ServiceRunTasksSession(AbstractServiceSession):
    """
    Implementation of RunTasksSession that talks to a
    gRPC service.  This is largely only used by command-line tests.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, host: str = None,
                 port: str = None,
                 timeout_in_seconds: int = 30,
                 metadata: Dict[str, str] = None,
                 security_cfg: Dict[str, Any] = None,
                 umbrella_timeout: Timeout = None):
        """
        Creates a RunTasksSession that connects to the
        Task Service and delegates its implementations to the service.

        :param host: the service host to connect to
                     If None, will use a default
        :param port: the service port
                     If None, will use a default
        :param timeout_in_seconds: timeout to use when communicating
                with the service
        :param metadata: A grpc metadata of key/value pairs to be inserted into
                         the header. Default is None. Preferred format is a
                         dictionary of string keys to string values.
        :param security_cfg: An optional dictionary of parameters used to
                        secure the TLS and the authentication of the gRPC
                        connection.  Supplying this implies use of a secure
                        GRPC Channel.  Default is None, uses insecure channel.
        :param umbrella_timeout: A Timeout object under which the length of all
                        looping and retries should be considered
        """
        use_host: str = "localhost"
        if host is not None:
            use_host = host

        use_port: str = "30012"
        if port is not None:
            use_port = port

        AbstractServiceSession.__init__(self, "Run Tasks Server",
                                        service_stub.TaskServiceStub,
                                        use_host, use_port,
                                        timeout_in_seconds, metadata,
                                        security_cfg, umbrella_timeout)

        # Dictionary for decoding gRPC call results back to TaskStatus values -
        # we can deal with both string names and integer values for TaskStatus enums:
        self.task_status_decode: Dict[Any, TaskStatus] = {}
        self._map_status_value(service_messages.TaskStatus.UNKNOWN, TaskStatus.TASK_UNKNOWN)
        self._map_status_value(service_messages.TaskStatus.RUNNING, TaskStatus.TASK_RUNNING)
        self._map_status_value(service_messages.TaskStatus.SUCCESS, TaskStatus.TASK_SUCCESS)
        self._map_status_value(service_messages.TaskStatus.ERROR, TaskStatus.TASK_ERROR)
        self._map_status_value(service_messages.TaskStatus.INVALID_INPUT, TaskStatus.TASK_INVALID_INPUT)
        self._map_status_value(service_messages.TaskStatus.ALREADY_EXISTS, TaskStatus.TASK_ALREADY_EXISTS)
        self._map_status_value(service_messages.TaskStatus.DOES_NOT_EXIST, TaskStatus.TASK_DOES_NOT_EXIST)

    def _map_status_value(self,
                          grpc_enum: service_messages.TaskStatus,
                          service_enum: TaskStatus):
        """
        Setup decoding table for a mapping
        from protobuf-defined value of TaskStatus to internal service TaskStatus value
        :param grpc_enum: a value of service_messages.TaskStatus;
        :param service_enum: a value of service TaskStatus;
        :return: nothing
        """
        self.task_status_decode[int(grpc_enum)] = service_enum
        self.task_status_decode[service_messages.TaskStatus.Name(grpc_enum)] =\
            service_enum

    def generate_dataset(
            self,
            task_id: str,
            code_source: str,
            destination_uri: str,
            params: Dict[str, Any]) -> Tuple[TaskStatus, str]:
        """
        Execute "generate dataset" request
        :param task_id: task ID;
        :param code_source: Python code in text form used to generate dataset;
        :param destination_uri: URI for generated file destination;
        :param params: dictionary with optional request parameters;
        :return: tuple of 2 values:
                 status of executed request;
                 error message if some error has occurred;
                 None otherwise.
        """
        # Construct request dictionary:
        request_dict: Dict[str, Any] = \
            {
                "task_id": task_id,
                "code_source": code_source,
                "destination_uri": destination_uri,
                "params": {}
            }
        # pylint: disable=no-member
        result_dict: Dict[str, Any] = self.call_grpc_method(
            "generate_dataset",
            self._generate_dataset_from_stub,
            request_dict,
            service_messages.DatasetTaskRequest())
        if result_dict is None:
            return TaskStatus.TASK_ERROR, f"No result returned for task {task_id}"
        # Decode request result back into TaskStatus enum:
        status_value = result_dict.get("status", TaskStatus.TASK_UNKNOWN.value)
        status: TaskStatus = self.task_status_decode.get(status_value, TaskStatus.TASK_UNKNOWN)
        error_msg: str = result_dict.get("error_msg", None)
        return status, error_msg

    def get_task_status(self, task_id: str) -> Tuple[TaskStatus, str]:
        """
        Get task status request
        :param task_id: task ID;
        :return: tuple of 2 values:
                 status of the task with given ID;
                 error message if some error has occurred;
                 None otherwise.
        """
        # Construct request dictionary:
        request_dict: Dict[str, Any] = \
            {
                "task_id": task_id
            }
        # pylint: disable=no-member
        result_dict: Dict[str, Any] = self.call_grpc_method(
            "get_task_status",
            self._get_task_status_from_stub,
            request_dict,
            service_messages.TaskStatusRequest())
        if result_dict is None:
            return TaskStatus.TASK_ERROR, f"No result returned for task {task_id}"
        # Decode request result back into TaskStatus enum:
        status_value = result_dict.get("status", TaskStatus.TASK_UNKNOWN.value)
        status: TaskStatus = self.task_status_decode.get(status_value, TaskStatus.TASK_UNKNOWN)
        error_msg: str = result_dict.get("error_msg", None)
        return status, error_msg

    @staticmethod
    def _generate_dataset_from_stub(stub, timeout_in_seconds,
                                    metadata, credentials, *args):
        """
        Global method associated with the session that calls GenerateDataset
        given a grpc Stub already set up with a channel (socket) to call with.
        """
        response = stub.GenerateDataset(*args, timeout=timeout_in_seconds,
                                        metadata=metadata,
                                        credentials=credentials)
        return response

    @staticmethod
    def _get_task_status_from_stub(stub, timeout_in_seconds,
                                   metadata, credentials, *args):
        """
        Global method associated with the session that calls TaskStatusRequest
        given a grpc Stub already set up with a channel (socket) to call with.
        """
        response = stub.GetTaskStatus(*args, timeout=timeout_in_seconds,
                                      metadata=metadata,
                                      credentials=credentials)
        return response
