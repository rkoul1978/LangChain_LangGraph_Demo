"""Streamlit UI: upload a JSON file and let the agent create a JIRA ticket."""

from __future__ import annotations

import json

import streamlit as st
from dotenv import load_dotenv

from agent import run_agent

load_dotenv()

st.set_page_config(page_title="JSON → JIRA Agent", page_icon="🎫")

st.title("🎫 JSON → JIRA Ticket Agent")
st.caption("Powered by LangChain + LangGraph")

st.markdown(
    "Upload a JSON file describing a ticket. The agent will read it and create a "
    "JIRA issue for you."
)

with st.expander("Expected JSON shape"):
    st.code(
        json.dumps(
            {
                "project_key": "ENG",
                "summary": "Login button is misaligned on mobile",
                "description": "On screens < 400px the login button overflows.",
                "issue_type": "Bug",
                "priority": "High",
                "labels": ["ui", "mobile"],
            },
            indent=2,
        ),
        language="json",
    )

uploaded = st.file_uploader("Upload ticket JSON", type=["json"])

payload = None
if uploaded is not None:
    try:
        payload = json.loads(uploaded.read().decode("utf-8"))
        st.subheader("Parsed payload")
        st.json(payload)
    except json.JSONDecodeError as exc:
        st.error(f"Invalid JSON file: {exc}")

if st.button("Create JIRA ticket", type="primary", disabled=payload is None):
    if not isinstance(payload, dict):
        st.error("JSON must be an object with ticket fields.")
    else:
        with st.spinner("Agent is creating the ticket..."):
            try:
                result = run_agent(payload)
            except Exception as exc:  # surface any runtime error in the UI
                st.error(f"Something went wrong: {exc}")
            else:
                if result.strip().upper().startswith("ERROR"):
                    st.error(result)
                else:
                    st.success(result)
