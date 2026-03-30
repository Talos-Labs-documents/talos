from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class StepState:
    step_id: str
    description: str
    action_type: str
    status: str = "pending"
    output_data: str | None = None
    retries: int = 0


@dataclass
class TaskState:
    task_id: str
    user_goal: str
    task_type: str
    status: str
    steps: list[StepState] = field(default_factory=list)
    outputs: list = field(default_factory=list)
    failure_reason: str | None = None

    @classmethod
    def from_plan(cls, user_goal, task_type, plan):
        return cls(
            task_id=str(uuid4()),
            user_goal=user_goal,
            task_type=task_type,
            status="running",
            steps=plan,
        )

    def record(self, step, result):
        step.output_data = result
        step.status = "done"
        self.outputs.append(result)

    def fail(self, reason):
        self.status = "failed"
        self.failure_reason = reason