from enum import Enum


class TaskType(str, Enum):
    CHAT = "chat"
    PLANNING = "planning"
    CODING = "coding"
    DEBUGGING = "debugging"


class EvaluationStatus(str, Enum):
    PASS = "pass"
    RETRY = "retry"
    FAIL = "fail"