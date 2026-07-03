"""LangGraph agent that turns an uploaded JSON payload into a JIRA ticket.

The agent uses a ReAct-style graph: an LLM decides how to map the incoming JSON
to the `create_jira_ticket` tool and then calls it. A deterministic fallback is
provided for running without an LLM (useful for tests / offline mode).
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from tools import create_jira_ticket


def _build_llm():
    """Create a chat model. Returns None if no provider is configured."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
        )

    if provider == "azure" and os.getenv("AZURE_OPENAI_API_KEY"):
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
            temperature=0,
        )

    return None


SYSTEM_PROMPT = (
    "You are an assistant that creates JIRA tickets from JSON input. "
    "Read the JSON the user provides, map its fields to the create_jira_ticket "
    "tool arguments (project_key, summary, description, issue_type, priority, "
    "labels, assignee_account_id), and call the tool exactly once. "
    "If a required field (project_key or summary) is missing, explain what is "
    "missing instead of calling the tool."
)


def build_agent():
    """Build a LangGraph ReAct agent bound to the JIRA tool.

    Returns None when no LLM is configured so callers can use the fallback.
    """
    llm = _build_llm()
    if llm is None:
        return None

    from langgraph.prebuilt import create_react_agent

    return create_react_agent(llm, tools=[create_jira_ticket], prompt=SYSTEM_PROMPT) # langgraph


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Map common JSON key aliases onto the tool's expected argument names."""
    aliases = {
        "project": "project_key",
        "projectKey": "project_key",
        "project_key": "project_key",
        "title": "summary",
        "summary": "summary",
        "description": "description",
        "details": "description",
        "type": "issue_type",
        "issueType": "issue_type",
        "issue_type": "issue_type",
        "priority": "priority",
        "labels": "labels",
        "tags": "labels",
        "assignee": "assignee_account_id",
        "assignee_account_id": "assignee_account_id",
    }
    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        target = aliases.get(key, key)
        normalized[target] = value
    return normalized


def run_agent(payload: dict[str, Any]) -> str:
    """Run the agent on a JSON payload and return a human-readable result.

    Falls back to a direct tool call when no LLM is configured.
    """
    agent = build_agent()

    if agent is None:
        # Deterministic fallback: map fields and call the tool directly.
        args = _normalize_payload(payload)
        return create_jira_ticket.invoke(args)

    user_message = (
        "Create a JIRA ticket from this JSON payload:\n"
        f"```json\n{json.dumps(payload, indent=2)}\n```"
    )
    result = agent.invoke({"messages": [("user", user_message)]})  # langgraph
    messages = result.get("messages", [])
    if messages:
        return getattr(messages[-1], "content", str(messages[-1]))
    return "No response produced by the agent."


def run_agent_from_json_string(raw: str) -> str:
    """Parse a JSON string and run the agent. Raises ValueError on bad JSON."""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object with ticket fields.")
    return run_agent(payload)
