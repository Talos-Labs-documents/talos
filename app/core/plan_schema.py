from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional
import json


STEP_STATUSES = {
    "pending",
    "approved",
    "running",
    "done",
    "failed",
    "manual_review",
}

PLAN_STATUSES = {
    "pending",
    "approved",
    "completed",
    "failed",
    "rejected",
}


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class PlanStep:
    step: int
    action: str
    target: str
    reason: str
    status: str = "pending"
    result: Optional[str] = None

    def __post_init__(self) -> None:
        if self.status not in STEP_STATUSES:
            self.status = "pending"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PlanStep":
        return cls(
            step=int(data.get("step", 0)),
            action=str(data.get("action", "manual_review")),
            target=str(data.get("target", "")),
            reason=str(data.get("reason", "")),
            status=str(data.get("status", "pending")),
            result=data.get("result"),
        )


@dataclass
class ExecutionPlan:
    goal: str
    status: str = "pending"
    created_at: str = field(default_factory=utc_now_iso)
    approved_at: Optional[str] = None
    steps: list[PlanStep] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in PLAN_STATUSES:
            self.status = "pending"

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "status": self.status,
            "created_at": self.created_at,
            "approved_at": self.approved_at,
            "steps": [step.to_dict() for step in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionPlan":
        raw_steps = data.get("steps", [])
        steps = [PlanStep.from_dict(step) for step in raw_steps]

        return cls(
            goal=str(data.get("goal", "")),
            status=str(data.get("status", "pending")),
            created_at=str(data.get("created_at", utc_now_iso())),
            approved_at=data.get("approved_at"),
            steps=steps,
        )


def save_plan(plan: ExecutionPlan, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
    return path


def load_plan(path: str | Path) -> ExecutionPlan:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return ExecutionPlan.from_dict(data)


def plan_exists(path: str | Path) -> bool:
    return Path(path).exists()


def delete_plan(path: str | Path) -> None:
    path = Path(path)
    if path.exists():
        path.unlink()


def format_plan(plan: ExecutionPlan) -> str:
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("TALOS EXECUTION PLAN")
    lines.append("=" * 60)
    lines.append(f"Goal       : {plan.goal}")
    lines.append(f"Status     : {plan.status}")
    lines.append(f"Created    : {plan.created_at}")
    if plan.approved_at:
        lines.append(f"Approved   : {plan.approved_at}")
    lines.append("")

    if not plan.steps:
        lines.append("No steps in plan.")
        return "\n".join(lines)

    lines.append("Steps:")
    for step in plan.steps:
        lines.append(f"  [{step.step}] {step.action}")
        lines.append(f"      target : {step.target}")
        lines.append(f"      reason : {step.reason}")
        lines.append(f"      status : {step.status}")
        if step.result:
            lines.append(f"      result : {step.result}")
        lines.append("")

    return "\n".join(lines).rstrip()


def make_fallback_plan(goal: str, reason: str) -> ExecutionPlan:
    return ExecutionPlan(
        goal=goal,
        status="pending",
        steps=[
            PlanStep(
                step=1,
                action="manual_review",
                target="(unspecified)",
                reason=reason,
                status="manual_review",
            )
        ],
    )