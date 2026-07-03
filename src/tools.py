"""LangChain tool that creates a JIRA ticket from structured ticket data."""

from __future__ import annotations

from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from jira_client import JiraApiError, JiraClient, JiraConfigError


class TicketInput(BaseModel):
    """Schema describing the fields used to create a JIRA ticket."""

    project_key: str = Field(..., description="JIRA project key, e.g. 'ENG' or 'OPS'.")
    summary: str = Field(..., description="Short, one-line summary / title of the ticket.")
    description: str = Field("", description="Detailed description of the issue.")
    issue_type: str = Field("Task", description="Issue type: Task, Bug, Story, etc.")
    priority: Optional[str] = Field(
        None, description="Priority name, e.g. Highest, High, Medium, Low."
    )
    labels: Optional[list[str]] = Field(
        None, description="Optional list of labels to attach to the ticket."
    )
    assignee_account_id: Optional[str] = Field(
        None, description="Optional JIRA account id of the assignee."
    )


@tool("create_jira_ticket", args_schema=TicketInput)
def create_jira_ticket(
    project_key: str,
    summary: str,
    description: str = "",
    issue_type: str = "Task",
    priority: Optional[str] = None,
    labels: Optional[list[str]] = None,
    assignee_account_id: Optional[str] = None,
) -> str:
    """Create a JIRA ticket and return the created issue key and URL.

    Use this whenever the user provides ticket details (from a JSON file or text)
    and wants a JIRA issue created.
    """
    try:
        client = JiraClient()
        result = client.create_issue(
            project_key=project_key,
            summary=summary,
            issue_type=issue_type,
            description=description,
            priority=priority,
            labels=labels,
            assignee_account_id=assignee_account_id,
        )
    except (JiraConfigError, JiraApiError) as exc:
        return f"ERROR: {exc}"

    return (
        f"Created JIRA ticket {result['key']} ({result['url']}). "
        f"Issue id: {result['id']}."
    )
