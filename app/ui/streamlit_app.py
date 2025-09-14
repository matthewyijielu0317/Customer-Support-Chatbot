import json
import time
from typing import Any, Dict

import requests
import streamlit as st


API_BASE = st.secrets.get("API_BASE", "http://localhost:8000/v1")


def chat(query: str) -> Dict[str, Any]:
    resp = requests.post(f"{API_BASE}/chat", json={"query": query}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def main():
    st.set_page_config(page_title="Customer Support Chatbot", page_icon="🤖")
    st.title("Customer Support Chatbot (Template)")

    question = st.text_input("Ask a question")
    if st.button("Send") and question:
        with st.spinner("Thinking..."):
            t0 = time.time()
            data = chat(question)
            dt = time.time() - t0
        st.success(data.get("answer", "No answer"))
        with st.expander("Details"):
            st.code(json.dumps(data, indent=2))
        st.caption(f"Latency: {dt:.2f}s")


if __name__ == "__main__":
    main()


