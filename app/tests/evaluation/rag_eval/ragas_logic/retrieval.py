from typing import Any


def normalize_agent_result(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize agent output into stable answer, context, and source fields."""
    return {
        "answer": str(result.get("output", result.get("answer", "")) or ""),
        "contexts": [str(value) for value in result.get("contexts", [])],
        "sources": [str(value) for value in result.get("sources", [])],
    }

