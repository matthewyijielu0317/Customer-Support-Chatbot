"""Tests for the reranker functionality."""

import pytest
from unittest.mock import Mock, patch

from src.retrievers.reranker import Reranker


@pytest.fixture
def sample_docs():
    """Sample documents for testing."""
    return [
        {"text": "This document is about shipping policies and delivery times.", "source": "shipping.pdf"},
        {"text": "Product returns can be made within 30 days of purchase.", "source": "returns.pdf"},
        {"text": "Payment processing and billing information is handled securely.", "source": "billing.pdf"},
    ]


@patch('src.retrievers.reranker.CrossEncoder')
def test_reranker_initialization(mock_cross_encoder):
    """Test that reranker initializes correctly."""
    mock_model = Mock()
    mock_cross_encoder.return_value = mock_model
    
    reranker = Reranker()
    
    mock_cross_encoder.assert_called_once_with("cross-encoder/ms-marco-MiniLM-L-6-v2")
    assert reranker._cross_encoder == mock_model


@patch('src.retrievers.reranker.CrossEncoder')
def test_reranker_rerank_empty_docs(mock_cross_encoder):
    """Test that reranker handles empty document list."""
    mock_model = Mock()
    mock_cross_encoder.return_value = mock_model
    
    reranker = Reranker()
    result = reranker.rerank("test query", [])
    
    assert result == []
    mock_model.predict.assert_not_called()


@patch('src.retrievers.reranker.CrossEncoder')
def test_reranker_rerank_documents(mock_cross_encoder, sample_docs):
    """Test that reranker correctly reranks documents."""
    mock_model = Mock()
    mock_model.predict.return_value = [0.8, 0.3, 0.6]  # High, low, medium scores
    mock_cross_encoder.return_value = mock_model
    
    reranker = Reranker()
    result = reranker.rerank("shipping delivery", sample_docs, top_k=2)
    
    # Should return top 2 documents ordered by score
    assert len(result) == 2
    assert result[0]["source"] == "shipping.pdf"  # Highest score (0.8)
    assert result[1]["source"] == "billing.pdf"   # Medium score (0.6)
    assert result[0]["rerank_score"] == 0.8
    assert result[1]["rerank_score"] == 0.6
    
    # Check that predict was called with correct pairs
    expected_pairs = [
        ("shipping delivery", "This document is about shipping policies and delivery times."),
        ("shipping delivery", "Product returns can be made within 30 days of purchase."),
        ("shipping delivery", "Payment processing and billing information is handled securely."),
    ]
    mock_model.predict.assert_called_once_with(expected_pairs, show_progress_bar=False)


@patch('src.retrievers.reranker.CrossEncoder')
def test_reranker_no_top_k_limit(mock_cross_encoder, sample_docs):
    """Test reranker without top_k limit returns all documents."""
    mock_model = Mock()
    mock_model.predict.return_value = [0.8, 0.3, 0.6]
    mock_cross_encoder.return_value = mock_model
    
    reranker = Reranker()
    result = reranker.rerank("test query", sample_docs)
    
    # Should return all documents, reordered by score
    assert len(result) == 3
    assert [doc["rerank_score"] for doc in result] == [0.8, 0.6, 0.3]


def test_reranker_import_error():
    """Test that RuntimeError is properly raised when sentence-transformers is not available."""
    with patch('src.retrievers.reranker.CrossEncoder', side_effect=ImportError("No module")):
        with pytest.raises(RuntimeError, match="Failed to load CrossEncoder model"):
            from src.retrievers.reranker import Reranker
            Reranker()
