from app.types import TaskType


def classify_intent(text: str):
    t = text.lower()

    if "plan" in t or "architecture" in t:
        return TaskType.PLANNING
    if "code" in t or "build" in t:
        return TaskType.CODING
    if "error" in t or "debug" in t:
        return TaskType.DEBUGGING

    return TaskType.CHAT