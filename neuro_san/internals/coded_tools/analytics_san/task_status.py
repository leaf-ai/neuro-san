# Copyright (C) 2019-2024 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
#
# This software is a trade secret, and contains proprietary and confidential
# materials of Cognizant Digital Business Evolutionary AI.
# Cognizant Digital Business prohibits the use, transmission, copying,
# distribution, or modification of this software outside of the
# Cognizant Digital Business EAI organization.
#
# END COPYRIGHT
"""
Comments in class description
"""
from enum import Enum


class TaskStatus(Enum):
    """
    Class enumerating possible status of LLM task request
    """
    TASK_UNKNOWN = 0
    TASK_RUNNING = 1
    TASK_SUCCESS = 2
    TASK_ERROR = 3
    TASK_INVALID_INPUT = 4
    TASK_ALREADY_EXISTS = 5
    TASK_DOES_NOT_EXIST = 6
