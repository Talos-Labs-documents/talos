from __future__ import annotations

from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path.cwd().resolve()
OUTPUTS_DIR = WORKSPACE_ROOT / "data" / "outputs"


def tool_result(success: bool, output: Any = None, error: str | None = None) -> dict[str, Any]:
    return {
        "success": success,
        "output": output,
        "error": error,
    }


def safe_path(user_path: str) -> Path:
    """
    Resolve a user-supplied path safely inside the current workspace.
    Raises ValueError if the path is empty or escapes the workspace root.
    """
    if not user_path or not user_path.strip():
        raise ValueError("Path is empty.")

    candidate = (WORKSPACE_ROOT / user_path).resolve()

    if candidate != WORKSPACE_ROOT and WORKSPACE_ROOT not in candidate.parents:
        raise ValueError(f"Path escapes workspace: {user_path}")

    return candidate


def safe_output_path(filename: str) -> Path:
    """
    Force file writes into data/outputs/ using only the basename.
    """
    clean_name = Path(filename).name.strip()

    if not clean_name:
        raise ValueError("Output filename is empty.")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    return (OUTPUTS_DIR / clean_name).resolve()


def list_dir(path: str = ".") -> dict[str, Any]:
    try:
        target = safe_path(path)

        if not target.exists():
            return tool_result(False, error=f"Directory does not exist: {path}")

        if not target.is_dir():
            return tool_result(False, error=f"Not a directory: {path}")

        items: list[str] = []
        for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            item_type = "dir" if item.is_dir() else "file"
            rel_path = item.relative_to(WORKSPACE_ROOT)
            items.append(f"[{item_type}] {rel_path}")

        output = "\n".join(items) if items else "(empty directory)"
        return tool_result(True, output=output)

    except Exception as exc:
        return tool_result(False, error=str(exc))


def read_file(path: str, max_chars: int = 20000) -> dict[str, Any]:
    try:
        target = safe_path(path)

        if not target.exists():
            return tool_result(False, error=f"File does not exist: {path}")

        if not target.is_file():
            return tool_result(False, error=f"Not a file: {path}")

        text = target.read_text(encoding="utf-8")

        truncated = False
        if len(text) > max_chars:
            text = text[:max_chars]
            truncated = True

        if truncated:
            text += "\n\n[TRUNCATED FOR SAFETY]"

        return tool_result(True, output=text)

    except UnicodeDecodeError:
        return tool_result(False, error=f"File is not a UTF-8 text file: {path}")
    except Exception as exc:
        return tool_result(False, error=str(exc))


def write_file(path: str, content: str, force_outputs_dir: bool = True) -> dict[str, Any]:
    """
    By default, writes only into data/outputs/.

    Example:
        write_file("report.md", "hello")
        -> data/outputs/report.md
    """
    try:
        if content is None or not str(content).strip():
            return tool_result(False, error="No content provided to write.")

        if force_outputs_dir:
            target = safe_output_path(path)
        else:
            target = safe_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)

        target.write_text(str(content), encoding="utf-8")

        rel_path = target.relative_to(WORKSPACE_ROOT)
        return tool_result(True, output=f"Wrote file: {rel_path}")

    except Exception as exc:
        return tool_result(False, error=str(exc))


def summarize_text(text: str, ollama_client) -> dict[str, Any]:
    """
    Summarize text using the provided Ollama client.

    Expected client interface:
        generate(prompt: str) -> str
    """
    try:
        if not text or not text.strip():
            return tool_result(False, error="No text provided to summarize.")

        prompt = f"""
You are TALOS, a precise local execution agent.

Analyze the following text and produce:

1. A concise summary (3-5 sentences max)
2. Concrete weaknesses or missing elements (if none, say "None identified")
3. Clear next-step action items (bullet points)

Be direct. Avoid fluff. No filler language.

TEXT:
{text}
""".strip()

        if hasattr(ollama_client, "generate"):
            summary = ollama_client.generate(prompt)
        elif hasattr(ollama_client, "chat"):
            summary = ollama_client.chat(prompt)
        elif hasattr(ollama_client, "complete"):
            summary = ollama_client.complete(prompt)
        else:
            return tool_result(
                False,
                error="ollama_client must expose generate(), chat(), or complete().",
            )

        if summary is None or not str(summary).strip():
            return tool_result(False, error="Model returned an empty summary.")

        return tool_result(True, output=str(summary).strip())

    except Exception as exc:
        return tool_result(False, error=str(exc))


def inspect_workspace_root() -> dict[str, Any]:
    try:
        return tool_result(True, output=str(WORKSPACE_ROOT))
    except Exception as exc:
        return tool_result(False, error=str(exc))