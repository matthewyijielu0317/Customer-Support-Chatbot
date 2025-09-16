import sys
from pathlib import Path


# Ensure project root is on sys.path so `src` imports resolve
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from typing import List

from src.graph.nodes.retrieve_docs import retrieve_docs_node
from src.graph.nodes.rerank_filter import rerank_filter_node
from src.graph.state import RAGState


def format_snippet(text: str, max_len: int = 300) -> str:
    if not text:
        return ""
    t = text.strip().replace("\n", " ")
    return t[:max_len] + ("…" if len(t) > max_len else "")


def print_results(header: str, docs: List[dict]) -> None:
    print(f"\n{header}")
    print(f"Retrieved {len(docs)} documents")
    top = min(len(docs), 5)
    for i in range(top):
        d = docs[i]
        src = d.get("source")
        title = d.get("title")
        page = d.get("page")
        score = d.get("score")
        rerank_score = d.get("rerank_score")
        snippet = format_snippet(d.get("text", ""))
        print("-" * 80)
        print(f"Result #{i+1}")
        print(f"  score: {score}")
        if rerank_score is not None:
            print(f"  rerank_score: {rerank_score}")
        print(f"  source: {src}")
        if title:
            print(f"  title: {title}")
        if page is not None:
            print(f"  page: {page}")
        print(f"  snippet: {snippet}")


def main() -> None:
    query = "how to refund"
    print(f"Query: {query}")
    state = RAGState(query=query)

    try:
        out_state = retrieve_docs_node(state)
    except Exception as e:
        print(f"Error during retrieval: {e}")
        sys.exit(1)

    docs_pre = [dict(d) for d in (out_state.docs or [])]
    print_results("Before rerank (retriever results)", docs_pre)

    try:
        out_state = rerank_filter_node(out_state)
    except Exception as e:
        print(f"Error during reranking: {e}")
        sys.exit(1)

    docs_post = out_state.docs or []
    print_results("After rerank (reranked results)", docs_post)


if __name__ == "__main__":
    main()


