from app.state.task_state import StepState


def create_plan(task_type, user_input):
    if task_type == "planning":
        return [
            StepState("1", "Understand the request", "analyze"),
            StepState("2", "Break into structure", "plan"),
            StepState("3", "Generate final output", "generate"),
        ]

    return [
        StepState("1", "Generate response", "generate")
    ]