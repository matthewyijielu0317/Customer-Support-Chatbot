import sys
from pathlib import Path

# Ensure project root is on sys.path for `src` imports
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.graph.graph import build_graph
from src.graph.state import RAGState


def main() -> None:
    graph = build_graph()
    queries = [
        "When can I get my refund?",
        "Where is my order?",
        "Hi there!",
        "What is your shipping policy?",
        "What is the weather in Tokyo?",
    ]

    for q in queries:
        state = RAGState(query=q)
        out = graph.invoke(state)

        def extract(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        intent = extract(out, "intent", "")
        docs = extract(out, "docs", []) or []
        answer = (extract(out, "answer", "") or "").strip()

        print(f"Q: {q}")
        grounded = extract(out, "grounded", None)
        print(f"Intent: {intent}  Docs: {len(docs)}  Grounded: {grounded}")
        print(answer)
        print("-" * 80)


if __name__ == "__main__":
    main()


