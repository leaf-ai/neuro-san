from typing import Any
from typing import Dict

import json

from neuro_san.internals.coded_tools.analytics_san.service_run_tasks_session import ServiceRunTasksSession


class GRPCTaskClient:
    """
    Class implementing inference request against gRPC server endpoint
    """

    def __init__(self, endpoint: str):
        parts = endpoint.split(":")
        self.session = ServiceRunTasksSession(parts[0], int(parts[1]))
        print(f"gRPC client created. Connected to: {endpoint}")

    def generate_dataset(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute request for dataset generation
        """
        task_id: str = request.get("task_id", None)
        code_source: str = request.get("code_source", None)
        destination_uri: str = request.get("destination_uri", None)
        params: Dict[str, str] = request.get("params", {})

        status, err_msg = self.session.generate_dataset(task_id, code_source, destination_uri, params)
        result: Dict[str, Any] = \
            {
                "task_id": task_id,
                "status": status.name,
            }
        if err_msg is not None:
            result["error_msg"] = err_msg
        print("GENERATE DATASET result:")
        print(f"{json.dumps(result, indent=4, sort_keys=True)}")
        return result

    def get_task_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute request for querying task status
        """
        task_id: str = request.get("task_id", None)

        status, err_msg = self.session.get_task_status(task_id)
        result: Dict[str, Any] = \
            {
                "task_id": task_id,
                "status": status.name
            }
        if err_msg is not None:
            result["error_msg"] = err_msg
        return result

