import sys
import json
from pathlib import Path

# Ensure project root is on sys.path for `src` imports
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.graph.graph import build_graph
from src.graph.state import RAGState


def shorten(text: str, max_len: int = 500) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def print_case(header: str, query: str) -> None:
    graph = build_graph()
    state = RAGState(query=query)
    out = graph.invoke(state)

    def extract(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # Unpack
    intent = extract(out, "intent", None)
    ents = extract(out, "entities", {}) or {}
    flags = {
        "should_retrieve": bool(extract(out, "should_retrieve", False)),
        "should_retrieve_sql": bool(extract(out, "should_retrieve_sql", False)),
        "should_retrieve_docs": bool(extract(out, "should_retrieve_docs", False)),
    }
    sql_rows = extract(out, "sql_rows", []) or []
    docs = extract(out, "docs", []) or []
    citations = extract(out, "citations", []) or []
    answer = (extract(out, "answer", "") or "").strip()
    grounded = extract(out, "grounded", None)
    grounded_explanation = extract(out, "grounded_explanation", None)

    print("=" * 100)
    print(f"{header}\nQ: {query}")
    print(f"Intent: {intent} | Entities: {json.dumps(ents)} | Flags: {flags}")

    # SQL rows
    print("\n[SQL ROWS]")
    if sql_rows:
        for i, row in enumerate(sql_rows[:5], start=1):
            print(f"- Row {i}: {json.dumps(row, default=str)}")
    else:
        print("(none)")

    # Docs
    print("\n[DOC CONTEXT]")
    if docs:
        for i, d in enumerate(docs[:3], start=1):
            header = f"[{i}] {(d.get('title') or '')} — {(d.get('source') or '')}"
            if d.get("page") is not None:
                header += f" (p.{d.get('page')})"
            snippet = shorten(d.get("text") or "", 400)
            print(header)
            print(snippet)
            print()
    else:
        print("(none)")

    # Citations
    print("[CITATIONS]")
    if citations:
        for c in citations[:8]:
            try:
                print(f"- {c.source} | {getattr(c, 'title', None)} | score={getattr(c, 'score', None)}")
            except Exception:
                try:
                    print(f"- {c.get('source')} | {c.get('title')} | score={c.get('score')}")
                except Exception:
                    print(f"- {c}")
    else:
        print("(none)")

    # Answer
    print("\n[ANSWER]")
    print(answer or "(empty)")

    # Groundedness
    print("\n[GROUNDING]")
    print(f"grounded={grounded} | {grounded_explanation}")
    print()


def main() -> None:
    cases = [
        ("ONLY SQL", "What’s the status of order 123 for nbaudrey3c@salon.com?"),
        ("ONLY DOCS", "What’s your return window for sale items?"),
        ("BOTH", "I was charged twice for order 456 for email \"gdemezat@gravatar.com\", what’s the refund policy?"),
        ("NONE (CLARIFY)", "I want to check my order status"),
    ]

    for header, query in cases:
        print_case(header, query)


if __name__ == "__main__":
    main()


