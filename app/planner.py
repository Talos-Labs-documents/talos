from __future__ import annotations

import json
import re
from typing import Any

from app.core.plan_schema import (
    ExecutionPlan,
    PlanStep,
    make_fallback_plan,
)


ALLOWED_ACTIONS = {
    "read_file",
    "write_file",
    "list_dir",
    "summarize_text",
    "manual_review",
}

MAX_STEPS = 5


def build_plan(goal: str, ollama_client) -> ExecutionPlan:
    """
    Build a structured ExecutionPlan from a freeform goal.

    Expected ollama_client interface:
        generate(prompt: str) -> str
    """
    goal = (goal or "").strip()
    if not goal:
        return make_fallback_plan(
            goal="(empty goal)",
            reason="No goal was provided to the planner.",
        )

    prompt = make_planner_prompt(goal)

    try:
        raw_response = _call_model(ollama_client, prompt)
        data = _extract_json(raw_response)

        if not isinstance(data, dict):
            return make_fallback_plan(
                goal=goal,
                reason="Planner did not return a valid JSON object.",
            )

        raw_steps = data.get("steps", [])
        if not isinstance(raw_steps, list) or not raw_steps:
            return make_fallback_plan(
                goal=goal,
                reason="Planner returned no usable steps.",
            )

        steps: list[PlanStep] = []
        for idx, raw_step in enumerate(raw_steps[:MAX_STEPS], start=1):
            if not isinstance(raw_step, dict):
                steps.append(
                    PlanStep(
                        step=idx,
                        action="manual_review",
                        target="(unspecified)",
                        reason="Planner returned a non-dictionary step.",
                        status="manual_review",
                    )
                )
                continue

            steps.append(normalize_step(raw_step, idx))

        if not steps:
            return make_fallback_plan(
                goal=goal,
                reason="Planner returned no valid normalized steps.",
            )

        normalized_goal = str(data.get("goal", goal)).strip() or goal

        return ExecutionPlan(
            goal=normalized_goal,
            status="pending",
            steps=steps,
        )

    except Exception as exc:
        return make_fallback_plan(
            goal=goal,
            reason=f"Planner error: {exc}",
        )


def make_planner_prompt(goal: str) -> str:
    """
    Strongly constrains the model to a tiny safe action vocabulary.
    """
    return f"""
You are TALOS, a careful local planning assistant.

Your job is to turn a user goal into a SMALL structured execution plan.

You may ONLY use these actions:
- read_file
- write_file
- list_dir
- summarize_text
- manual_review

Rules:
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include explanations outside the JSON.
- Keep plans short: 2 to 5 steps max.
- Prefer safe, file-based actions.
- If the request is unclear, use manual_review.
- write_file targets should be simple filenames like "report.md" or "summary.txt".
- For summarize_text, set target to the source file or "(from previous step)".
- Never invent dangerous actions like shell execution, deletion, web browsing, package installation, or system modification.
- Do not use read_file unless there is a concrete file path.
- If the user has not provided a concrete file or source text, prefer manual_review.

Return JSON in exactly this shape:
{{
  "goal": "user goal here",
  "steps": [
    {{
      "action": "read_file",
      "target": "README.md",
      "reason": "Read the file before analyzing it"
    }},
    {{
      "action": "summarize_text",
      "target": "README.md",
      "reason": "Summarize the contents and identify issues"
    }},
    {{
      "action": "write_file",
      "target": "README_summary.md",
      "reason": "Write the summary to an output file"
    }}
  ]
}}

User goal:
{goal}
""".strip()


def normalize_step(raw_step: dict[str, Any], index: int) -> PlanStep:
    action = str(raw_step.get("action", "manual_review")).strip()

    raw_target = raw_step.get("target", "(unspecified)")
    target = "(unspecified)" if raw_target is None else str(raw_target).strip()

    reason = str(raw_step.get("reason", "No reason provided.")).strip()

    action = normalize_action(action)

    # Prevent invalid file reads without a real file target.
    if action == "read_file" and target in {"(from previous step)", "(unspecified)", ""}:
        action = "manual_review"
        target = "(unspecified)"
        reason = "No concrete file target was provided for read_file."

    # If summarize_text has no clear source, force manual review.
    if action == "summarize_text" and target in {"None", "", "(unspecified)"}:
        action = "manual_review"
        target = "(unspecified)"
        reason = "Clarify the source text for summarization."

    if not target or target == "None":
        target = "(unspecified)"

    if not reason:
        reason = "No reason provided."

    if action == "write_file":
        target = normalize_output_filename(target)

    return PlanStep(
        step=index,
        action=action,
        target=target,
        reason=reason,
        status="manual_review" if action == "manual_review" else "pending",
    )


def normalize_action(action: str) -> str:
    action = action.lower().strip()

    aliases = {
        "read": "read_file",
        "readfile": "read_file",
        "open_file": "read_file",
        "open": "read_file",
        "list": "list_dir",
        "ls": "list_dir",
        "dir": "list_dir",
        "list_files": "list_dir",
        "write": "write_file",
        "writefile": "write_file",
        "save_file": "write_file",
        "save": "write_file",
        "summarize": "summarize_text",
        "summary": "summarize_text",
        "analyze_text": "summarize_text",
        "review": "manual_review",
        "manual": "manual_review",
    }

    action = aliases.get(action, action)

    if action not in ALLOWED_ACTIONS:
        return "manual_review"

    return action


def normalize_output_filename(target: str) -> str:
    """
    Keep write targets simple and safe.
    The actual write location is still enforced in tools.py.
    """
    target = target.strip()

    if not target or target in {"(unspecified)", "None"}:
        return "talos_output.md"

    # Strip directories and keep just the filename
    target = target.replace("\\", "/").split("/")[-1].strip()

    # Remove unsafe characters
    target = re.sub(r"[^A-Za-z0-9._-]", "_", target)

    if not target:
        target = "talos_output.md"

    # If no extension, default to markdown
    if "." not in target:
        target += ".md"

    return target


def _call_model(ollama_client, prompt: str) -> str:
    """
    Adapt this if your Ollama client method is different.
    """
    if hasattr(ollama_client, "generate"):
        result = ollama_client.generate(prompt)
    elif hasattr(ollama_client, "chat"):
        result = ollama_client.chat(prompt)
    elif hasattr(ollama_client, "complete"):
        result = ollama_client.complete(prompt)
    else:
        raise AttributeError(
            "ollama_client must expose generate(), chat(), or complete()."
        )

    if result is None:
        raise ValueError("Model returned None.")

    return str(result).strip()


def _extract_json(text: str) -> Any:
    """
    Attempts:
    1. direct json.loads(text)
    2. fenced-block removal then parse
    3. extract first {...} block and parse it
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Planner response was empty.")

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    cleaned = _strip_code_fences(text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        candidate = match.group(0)
        return json.loads(candidate)

    raise ValueError("Could not extract valid JSON from planner response.")


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()