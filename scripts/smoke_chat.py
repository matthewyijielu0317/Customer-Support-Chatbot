from src.graph.graph import build_graph
from src.graph.state import RAGState


def main() -> None:
    graph = build_graph()
    state = RAGState(query="What is your return policy?")
    out = graph.invoke(state)
    print(out.answer)


if __name__ == "__main__":
    main()


