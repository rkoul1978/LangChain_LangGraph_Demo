# JSON → JIRA Ticket Agent

A LangChain + LangGraph agent that accepts a JSON file from a UI and creates a
JIRA ticket from it.

## How it works

```
Streamlit UI  ──uploads JSON──▶  LangGraph ReAct agent  ──tool call──▶  JIRA REST API
   (app.py)                          (agent.py)              (tools.py / jira_client.py)
```

- **`src/app.py`** – Streamlit UI to upload a JSON file and trigger ticket creation.
- **`src/agent.py`** – LangGraph ReAct agent. An LLM maps the JSON fields to the
  tool arguments and calls the tool. Falls back to a deterministic field mapping
  when no LLM key is configured.
- **`src/tools.py`** – `create_jira_ticket` LangChain tool with a typed schema.
- **`src/jira_client.py`** – Minimal JIRA Cloud REST client.
- **`src/main.py`** – Optional CLI entry point.

## Setup

1. Create and activate a virtual environment, then install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Configure credentials:

   ```powershell
   Copy-Item .env.example .env
   ```

   Edit `.env` and set `JIRA_BASE_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN`
   (create a token at https://id.atlassian.com/manage-profile/security/api-tokens).
   Optionally set `OPENAI_API_KEY` to enable the LLM-driven agent.

## Run the UI

```powershell
streamlit run src/app.py
```

Upload `sample_ticket.json` (or your own) and click **Create JIRA ticket**.

## Run from the CLI

```powershell
python src/main.py sample_ticket.json
```

## Expected JSON shape

```json
{
  "project_key": "ENG",
  "summary": "Login button is misaligned on mobile",
  "description": "Detailed description of the issue.",
  "issue_type": "Bug",
  "priority": "High",
  "labels": ["ui", "mobile"]
}
```

Common aliases are also accepted (`project`/`projectKey`, `title`, `tags`, `type`).

## Notes

- Without an LLM key the agent still works: it deterministically maps JSON fields
  to the tool and creates the ticket.
- The JIRA client targets JIRA **Cloud** REST API v3 (descriptions use ADF).
