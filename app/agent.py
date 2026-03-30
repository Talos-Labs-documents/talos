from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from app.core.plan_schema import (
    ExecutionPlan,
    PlanStep,
    delete_plan,
    load_plan,
    plan_exists,
    save_plan,
)
from app.planner import build_plan
from app.tools import list_dir, read_file, summarize_text, write_file


PENDING_PLAN_PATH = Path("data/plans/pending_plan.json")
LOGS_DIR = Path("data/logs")


class Agent:
    def __init__(self, ollama_client) -> None:
        self.ollama_client = ollama_client

    # -----------------------------
    # Public API
    # -----------------------------
    def create_pending_plan(self, goal: str) -> ExecutionPlan:
        plan = build_plan(goal, self.ollama_client)
        save_plan(plan, PENDING_PLAN_PATH)
        return plan

    def get_pending_plan(self) -> ExecutionPlan | None:
        if not plan_exists(PENDING_PLAN_PATH):
            return None
        return load_plan(PENDING_PLAN_PATH)

    def reject_pending_plan(self) -> bool:
        if not plan_exists(PENDING_PLAN_PATH):
            return False

        plan = load_plan(PENDING_PLAN_PATH)
        plan.status = "rejected"
        save_plan(plan, PENDING_PLAN_PATH)

        # for now we delete it after marking rejected
        delete_plan(PENDING_PLAN_PATH)
        return True

    def approve_pending_plan(self) -> dict[str, Any]:
        if not plan_exists(PENDING_PLAN_PATH):
            return {
                "success": False,
                "message": "No pending plan found.",
                "plan": None,
                "log_path": None,
            }

        plan = load_plan(PENDING_PLAN_PATH)
        plan.status = "approved"
        plan.approved_at = utc_now_iso()

        for step in plan.steps:
            if step.status == "pending":
                step.status = "approved"

        save_plan(plan, PENDING_PLAN_PATH)

        result = self.execute_plan(plan)

        # save final state
        save_plan(plan, PENDING_PLAN_PATH)

        return result

    def run_dry_plan(self, goal: str) -> ExecutionPlan:
        return build_plan(goal, self.ollama_client)

    # -----------------------------
    # Execution
    # -----------------------------
    def execute_plan(self, plan: ExecutionPlan) -> dict[str, Any]:
        log_path = self._make_log_path()
        context: dict[str, Any] = {
            "last_text": None,
            "last_summary": None,
            "last_dir_listing": None,
        }

        self._log(log_path, f"=== TALOS EXECUTION START ===")
        self._log(log_path, f"Goal: {plan.goal}")
        self._log(log_path, f"Status: {plan.status}")
        self._log(log_path, "")

        overall_success = True

        for step in plan.steps:
            # skip manual review steps automatically
            if step.action == "manual_review":
                step.status = "manual_review"
                step.result = "Step requires manual review."
                self._log(log_path, f"[STEP {step.step}] manual_review")
                self._log(log_path, f"  target: {step.target}")
                self._log(log_path, f"  result: {step.result}")
                self._log(log_path, "")
                overall_success = False
                continue

            step.status = "running"
            save_plan(plan, PENDING_PLAN_PATH)

            self._log(log_path, f"[STEP {step.step}] {step.action}")
            self._log(log_path, f"  target: {step.target}")
            self._log(log_path, f"  reason: {step.reason}")

            step_result = self.execute_step(step, context)

            if step_result["success"]:
                step.status = "done"
                step.result = stringify_result(step_result["output"])
                self._log(log_path, f"  status: done")
                self._log(log_path, f"  result: {step.result}")
            else:
                step.status = "failed"
                step.result = step_result["error"]
                self._log(log_path, f"  status: failed")
                self._log(log_path, f"  error: {step.result}")
                overall_success = False

            self._log(log_path, "")
            save_plan(plan, PENDING_PLAN_PATH)

        if overall_success and all(s.status == "done" for s in plan.steps):
            plan.status = "completed"
        else:
            plan.status = "failed"

        self._log(log_path, f"Final plan status: {plan.status}")
        self._log(log_path, f"=== TALOS EXECUTION END ===")

        return {
            "success": overall_success,
            "message": f"Plan execution finished with status: {plan.status}",
            "plan": plan,
            "log_path": str(log_path),
        }

    def execute_step(self, step: PlanStep, context: dict[str, Any]) -> dict[str, Any]:
        action = step.action
        target = step.target

        if action == "list_dir":
            result = list_dir("." if target in {"", "(unspecified)"} else target)
            if result["success"]:
                context["last_dir_listing"] = result["output"]
            return result

        if action == "read_file":
            result = read_file(target)
            if result["success"]:
                context["last_text"] = result["output"]
            return result

        if action == "summarize_text":
            text = context.get("last_text")
            if not text:
                return {
                    "success": False,
                    "output": None,
                    "error": "No prior text is available for summarize_text.",
                }

            result = summarize_text(text, self.ollama_client)
            if result["success"]:
                context["last_summary"] = result["output"]
            return result

        if action == "write_file":
            content = context.get("last_summary") or context.get("last_text")
            if not content:
                return {
                    "success": False,
                    "output": None,
                    "error": "No content available to write.",
                }

            return write_file(target, content, force_outputs_dir=True)

        return {
            "success": False,
            "output": None,
            "error": f"Unsupported action: {action}",
        }

    # -----------------------------
    # Logging helpers
    # -----------------------------
    def _make_log_path(self) -> Path:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
        return LOGS_DIR / f"run_{timestamp}.log"

    def _log(self, log_path: Path, message: str) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(message + "\n")


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def stringify_result(value: Any, max_len: int = 300) -> str:
    if value is None:
        return ""

    text = str(value).strip()
    if len(text) > max_len:
        return text[:max_len] + "... [truncated]"
    return text