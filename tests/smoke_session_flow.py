# save as scripts/smoke_session_flow.py (or run in a REPL)
import requests
from pprint import pprint

API_BASE = "http://localhost:8000/v1"
USER_ID = "alice@example.com"

def main():
    # 1) Create a session (FastAPI + Redis only)
    create_resp = requests.post(
        f"{API_BASE}/sessions",
        json={"user_id": USER_ID, "metadata": {"channel": "web"}},
        timeout=10,
    )
    create_resp.raise_for_status()
    session = create_resp.json()
    session_id = session["session_id"]
    print("Created:", session)

    # 2) Chat twice (messages live in Redis)
    payload = {"user_id": USER_ID, "session_id": session_id}
    for msg in ["Hi there!", "Can I return my order?"]:
        chat_resp = requests.post(
            f"{API_BASE}/chat",
            json={**payload, "query": msg},
            timeout=15,
        )
        chat_resp.raise_for_status()
        print("Chat turn:", chat_resp.json()["answer"])

    # 3) List active sessions (should show status=active)
    active = requests.get(
        f"{API_BASE}/sessions",
        params={"user_id": USER_ID},
        timeout=10,
    )
    active.raise_for_status()
    print("Active sessions:")
    pprint(active.json())

    # 4) Peek messages (pulled from Redis)
    history = requests.get(
        f"{API_BASE}/sessions/{session_id}/messages",
        params={"user_id": USER_ID, "limit": 10},
        timeout=10,
    )
    history.raise_for_status()
    print("Active transcript:")
    pprint(history.json())

    # 5) Close + archive (moves data into Mongo, clears Redis)
    close_resp = requests.post(
        f"{API_BASE}/sessions/{session_id}/close",
        params={"user_id": USER_ID},
        json={"summary": "Customer asked about returns"},
        timeout=10,
    )
    close_resp.raise_for_status()
    print("Closed:", close_resp.json())

    # 6) List with include_closed – you should see status=closed
    closed = requests.get(
        f"{API_BASE}/sessions",
        params={"user_id": USER_ID, "include_closed": "true"},
        timeout=10,
    )
    closed.raise_for_status()
    print("Including closed sessions:")
    pprint(closed.json())

    # 7) Messages now come from Mongo (Redis keys cleared)
    archived_history = requests.get(
        f"{API_BASE}/sessions/{session_id}/messages",
        params={"user_id": USER_ID},
        timeout=10,
    )
    archived_history.raise_for_status()
    print("Archived transcript:")
    pprint(archived_history.json())

if __name__ == "__main__":
    main()
