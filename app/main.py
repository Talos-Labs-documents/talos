from __future__ import annotations

import shlex
from pathlib import Path

from app.agent import Agent
from app.core.plan_schema import format_plan
from app.models.ollama_client import OllamaClient

VERSION = "TALOS 0.2 alpha"


def print_banner() -> None:
    print("=" * 60)
    print(VERSION)
    print("Local-first agent console with approval-gated execution")
    print("=" * 60)
    print("Type 'help' for commands.\n")


def print_help() -> None:
    print(
        """
Available commands:
  help
      Show this help menu

  status
      Show TALOS status and pending plan availability

  plantask <goal>
      Build a pending execution plan for a goal

  showplan
      Display the current pending plan

  approveplan
      Approve and execute the current pending plan

  rejectplan
      Reject and discard the current pending plan

  runplan <goal> --dry
      Generate and display a plan without saving or executing it

  showlog
      Show the newest execution log path

  exit
      Exit TALOS
""".strip()
    )
    print()


def latest_log_path() -> Path | None:
    logs_dir = Path("data/logs")
    if not logs_dir.exists():
        return None

    logs = sorted(logs_dir.glob("run_*.log"))
    if not logs:
        return None

    return logs[-1]


def print_status(agent: Agent) -> None:
    plan = agent.get_pending_plan()

    print("=" * 60)
    print("STATUS")
    print("=" * 60)
    print(f"Version      : {VERSION}")

    if plan is None:
        print("Pending plan : none")
    else:
        print("Pending plan : yes")
        print(f"Plan goal    : {plan.goal}")
        print(f"Plan status  : {plan.status}")
        print(f"Step count   : {len(plan.steps)}")

    log_path = latest_log_path()
    print(f"Latest log   : {log_path if log_path else 'none'}")
    print()


def handle_plantask(agent: Agent, goal: str) -> None:
    goal = goal.strip()
    if not goal:
        print("Usage: plantask <goal>\n")
        return

    plan = agent.create_pending_plan(goal)

    print("Pending plan created.\n")
    print(format_plan(plan))
    print()
    print("Use 'showplan' to inspect it again.")
    print("Use 'approveplan' to execute it.")
    print("Use 'rejectplan' to discard it.\n")


def handle_showplan(agent: Agent) -> None:
    plan = agent.get_pending_plan()
    if plan is None:
        print("No pending plan found.\n")
        return

    print(format_plan(plan))
    print()


def handle_approveplan(agent: Agent) -> None:
    result = agent.approve_pending_plan()

    if not result["success"] and result["plan"] is None:
        print(result["message"])
        print()
        return

    plan = result["plan"]
    log_path = result["log_path"]

    print(result["message"])
    print()

    if plan is not None:
        print(format_plan(plan))
        print()

    if log_path:
        print(f"Log file: {log_path}\n")


def handle_rejectplan(agent: Agent) -> None:
    ok = agent.reject_pending_plan()
    if ok:
        print("Pending plan rejected and discarded.\n")
    else:
        print("No pending plan found.\n")


def handle_runplan(agent: Agent, raw_args: list[str]) -> None:
    if not raw_args:
        print("Usage: runplan <goal> --dry\n")
        return

    is_dry = "--dry" in raw_args
    goal_parts = [part for part in raw_args if part != "--dry"]
    goal = " ".join(goal_parts).strip()

    if not goal:
        print("Usage: runplan <goal> --dry\n")
        return

    if not is_dry:
        print("For TALOS 0.2 alpha, runplan currently supports dry-run only.")
        print("Use: runplan <goal> --dry\n")
        return

    plan = agent.run_dry_plan(goal)
    print("Dry-run plan generated.\n")
    print(format_plan(plan))
    print()


def handle_showlog() -> None:
    log_path = latest_log_path()
    if log_path is None:
        print("No log files found.\n")
        return

    print(f"Latest log: {log_path}\n")


def build_agent() -> Agent:
    """
    Adjust this if your Ollama client requires different construction args.
    """
    ollama_client = OllamaClient()
    return Agent(ollama_client)


def main() -> None:
    agent = build_agent()
    print_banner()

    while True:
        try:
            raw = input("talos> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting TALOS.")
            break

        if not raw:
            continue

        try:
            parts = shlex.split(raw)
        except ValueError as exc:
            print(f"Input parse error: {exc}\n")
            continue

        command = parts[0].lower()
        args = parts[1:]

        if command in {"exit", "quit"}:
            print("Exiting TALOS.")
            break

        elif command == "help":
            print_help()

        elif command == "status":
            print_status(agent)

        elif command == "plantask":
            handle_plantask(agent, " ".join(args))

        elif command == "showplan":
            handle_showplan(agent)

        elif command in {"approveplan", "approve"}:
            handle_approveplan(agent)

        elif command == "rejectplan":
            handle_rejectplan(agent)

        elif command == "runplan":
            handle_runplan(agent, args)

        elif command == "showlog":
            handle_showlog()

        else:
            print(f"Unknown command: {command}")
            print("Type 'help' for available commands.\n")


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()