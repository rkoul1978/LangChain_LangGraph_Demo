"""Thin wrapper around the JIRA Cloud REST API for creating issues."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import requests
from requests.auth import HTTPBasicAuth


class JiraConfigError(RuntimeError):
    """Raised when the JIRA configuration is missing or invalid."""


class JiraApiError(RuntimeError):
    """Raised when the JIRA API returns an error response."""


@dataclass
class JiraConfig:
    base_url: str
    email: str
    api_token: str

    @classmethod
    def from_env(cls) -> "JiraConfig":
        base_url = os.getenv("JIRA_BASE_URL", "").strip().rstrip("/")
        email = os.getenv("JIRA_EMAIL", "").strip()
        api_token = os.getenv("JIRA_API_TOKEN", "").strip()

        missing = [
            name
            for name, value in (
                ("JIRA_BASE_URL", base_url),
                ("JIRA_EMAIL", email),
                ("JIRA_API_TOKEN", api_token),
            )
            if not value
        ]
        if missing:
            raise JiraConfigError(
                "Missing required environment variables: " + ", ".join(missing)
            )
        return cls(base_url=base_url, email=email, api_token=api_token)


class JiraClient:
    """Minimal JIRA Cloud client. Only implements what the agent needs."""

    def __init__(self, config: Optional[JiraConfig] = None, timeout: int = 30) -> None:
        self.config = config or JiraConfig.from_env()
        self.timeout = timeout
        self._auth = HTTPBasicAuth(self.config.email, self.config.api_token)

    def _to_adf(self, text: str) -> dict[str, Any]:
        """Convert plain text into Atlassian Document Format (required by Cloud)."""
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text or ""}],
                }
            ],
        }

    def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str = "Task",
        description: str = "",
        priority: Optional[str] = None,
        labels: Optional[list[str]] = None,
        assignee_account_id: Optional[str] = None,
        extra_fields: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Create a JIRA issue and return a summary dict with key, id and URL."""
        if not project_key:
            raise JiraConfigError("project_key is required to create a JIRA issue.")
        if not summary:
            raise JiraConfigError("summary is required to create a JIRA issue.")

        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": self._to_adf(description),
        }
        if priority:
            fields["priority"] = {"name": priority}
        if labels:
            fields["labels"] = labels
        if assignee_account_id:
            fields["assignee"] = {"id": assignee_account_id}
        if extra_fields:
            fields.update(extra_fields)

        url = f"{self.config.base_url}/rest/api/3/issue"
        response = requests.post(
            url,
            json={"fields": fields},
            auth=self._auth,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            raise JiraApiError(
                f"JIRA API returned {response.status_code}: {response.text}"
            )

        data = response.json()
        issue_key = data.get("key", "")
        return {
            "key": issue_key,
            "id": data.get("id", ""),
            "url": f"{self.config.base_url}/browse/{issue_key}" if issue_key else "",
            "self": data.get("self", ""),
        }
