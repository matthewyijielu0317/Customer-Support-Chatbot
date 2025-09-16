from pathlib import Path
import sys

# Ensure project root for `src` imports
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.graph.nodes.router import classify_intent


def main() -> None:
    samples = [
        "When can I get my refund?",
        "Where is my order?",
        "I need help with my account password.",
        "Hi there!",
        "What is your shipping policy?",
        "What is the weather in Tokyo?",
    ]
    for q in samples:
        intent = classify_intent(q)
        print(f"Q: {q}\n -> intent: {intent}\n")


if __name__ == "__main__":
    main()
