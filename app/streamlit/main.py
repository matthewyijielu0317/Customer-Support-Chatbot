from __future__ import annotations

import requests
import streamlit as st


DEFAULT_API_BASE = "http://localhost:8000"


def _get_sessions(base_url: str, user_id: str, include_closed: bool = False) -> list[dict]:
    params = {"user_id": user_id}
    if include_closed:
        params["include_closed"] = "true"
    resp = requests.get(f"{base_url}/v1/sessions", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("sessions", [])


def _create_session(base_url: str, user_id: str) -> dict:
    resp = requests.post(
        f"{base_url}/v1/sessions",
        json={"user_id": user_id},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def _get_messages(base_url: str, user_id: str, session_id: str) -> list[dict]:
    params = {"user_id": user_id}
    resp = requests.get(
        f"{base_url}/v1/sessions/{session_id}/messages",
        params=params,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("messages", [])


def _send_message(base_url: str, user_id: str, session_id: str | None, query: str) -> dict:
    payload = {"user_id": user_id, "query": query}
    if session_id:
        payload["session_id"] = session_id
    resp = requests.post(f"{base_url}/v1/chat", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _ensure_state():
    if "sessions" not in st.session_state:
        st.session_state.sessions = []
    if "selected_session" not in st.session_state:
        st.session_state.selected_session = None
    if "messages" not in st.session_state:
        st.session_state.messages = []


def _refresh_sessions(base_url: str, user_id: str):
    st.session_state.sessions = _get_sessions(base_url, user_id)
    if st.session_state.sessions and st.session_state.selected_session is None:
        st.session_state.selected_session = st.session_state.sessions[0]["session_id"]


def _refresh_messages(base_url: str, user_id: str, session_id: str | None):
    if not session_id:
        st.session_state.messages = []
        return
    st.session_state.messages = _get_messages(base_url, user_id, session_id)


def main() -> None:
    st.set_page_config(page_title="Customer Support Chatbot", layout="wide")
    _ensure_state()

    st.sidebar.title("Settings")
    base_url = st.sidebar.text_input("API Base URL", DEFAULT_API_BASE).strip()
    user_id = st.sidebar.text_input("User ID", st.session_state.get("user_id", "")).strip()

    if st.sidebar.button("Load sessions") and user_id:
        st.session_state.user_id = user_id
        _refresh_sessions(base_url, user_id)
        if st.session_state.selected_session:
            _refresh_messages(base_url, user_id, st.session_state.selected_session)

    if st.sidebar.button("New session") and user_id:
        session = _create_session(base_url, user_id)
        st.success(f"Started session {session['session_id']}")
        _refresh_sessions(base_url, user_id)
        st.session_state.selected_session = session["session_id"]
        st.session_state.messages = []

    include_closed = st.sidebar.checkbox("Include closed sessions", value=False)
    if include_closed and user_id:
        try:
            st.session_state.sessions = _get_sessions(base_url, user_id, include_closed=True)
        except requests.RequestException as exc:
            st.error(f"Failed to load sessions: {exc}")

    st.sidebar.subheader("Sessions")
    sessions = st.session_state.sessions
    if sessions:
        session_labels = [
            f"{s['session_id']} ({s.get('status', 'active')})" + (f"\nSummary: {s.get('summary', '')}" if s.get("summary") else "")
            for s in sessions
        ]
        selected_idx = None
        if st.session_state.selected_session:
            for idx, s in enumerate(sessions):
                if s["session_id"] == st.session_state.selected_session:
                    selected_idx = idx
                    break
        choice = st.sidebar.radio(
            "Select a session",
            options=range(len(sessions)),
            format_func=lambda i: session_labels[i],
            index=selected_idx if selected_idx is not None else 0,
        )
        selected_session = sessions[choice]["session_id"]
        if selected_session != st.session_state.selected_session:
            st.session_state.selected_session = selected_session
            _refresh_messages(base_url, user_id, selected_session)
    else:
        st.sidebar.write("No sessions loaded.")
        st.session_state.selected_session = None

    st.title("Customer Support Chat")
    if not user_id:
        st.info("Enter a user ID on the left to begin.")
        return

    session_id = st.session_state.selected_session
    st.write(f"**User:** {user_id}")
    st.write(f"**Session:** {session_id or 'new session'}")

    if st.session_state.messages:
        st.subheader("Conversation History")
        for msg in st.session_state.messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            st.markdown(f"**{role.capitalize()}:** {content}")
            if metadata := msg.get("metadata"):
                st.caption(f"Metadata: {metadata}")
    else:
        st.write("No messages yet.")

    st.subheader("Send a Message")
    with st.form("chat_form", clear_on_submit=True):
        query = st.text_area("Message", height=120)
        submitted = st.form_submit_button("Send")
        if submitted and query.strip():
            try:
                response = _send_message(base_url, user_id, session_id, query.strip())
            except requests.RequestException as exc:
                st.error(f"Failed to send message: {exc}")
            else:
                st.write("**Assistant:**", response.get("answer", ""))
                if response.get("citations"):
                    st.caption("Citations: " + ", ".join(c["source"] for c in response["citations"]))
                st.caption(f"Cache hit: {response.get('cache_hit')}")
                # Refresh state to include new turns
                _refresh_sessions(base_url, user_id)
                active_session = response.get("session_id")
                st.session_state.selected_session = active_session
                _refresh_messages(base_url, user_id, active_session)


if __name__ == "__main__":
    main()

