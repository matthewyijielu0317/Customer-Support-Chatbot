from src.graph.nodes.generate import generate_node
from src.graph.state import RAGState


def test_generate_node_requests_order_number_when_missing():
    state = RAGState(
        query="Where is my package?",
        query_type="needs_identifier",
        first_name="Alice",
    )

    result = generate_node(state)

    assert "order number" in result.answer.lower()
    assert result.answer.startswith("Alice")


def test_generate_node_skips_prompt_when_order_id_known():
    state = RAGState(
        query="Order 18 status",
        query_type="needs_identifier",
        order_id=18,
        sql_rows=[{"order_id": 18, "product_name": "Widget", "quantity": 1}],
    )

    result = generate_node(state)

    assert "order number" not in result.answer.lower()
