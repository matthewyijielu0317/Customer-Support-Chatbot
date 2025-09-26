"""Tests for the tabular ingestion API endpoint."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.api.main import app


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@patch('app.api.routes.ingest_tabular.create_engine_from_dsn')
@patch('app.api.routes.ingest_tabular.load_csvs')
@patch('app.api.routes.ingest_tabular.close_engine')
def test_ingest_tabular_success(mock_close, mock_load_csvs, mock_create_engine, client):
    """Test successful CSV ingestion via API."""
    # Mock the async functions
    mock_engine = AsyncMock()
    mock_create_engine.return_value = mock_engine
    mock_load_csvs.return_value = 150  # Total rows loaded
    mock_close.return_value = None
    
    # Make API request
    response = client.post("/v1/ingest/csv", json={
        "dsn": "postgresql://user:pass@localhost:5432/testdb",
        "customers_csv_path": "data/fake_customers.csv",
        "orders_csv_path": "data/fake_orders.csv",
        "products_csv_path": "data/fake_products.csv"
    })
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["rows_loaded"] == 150
    
    # Verify function calls
    mock_create_engine.assert_called_once_with("postgresql://user:pass@localhost:5432/testdb")
    mock_load_csvs.assert_called_once_with(
        mock_engine,
        "data/fake_customers.csv",
        "data/fake_orders.csv", 
        "data/fake_products.csv"
    )
    mock_close.assert_called_once_with(mock_engine)


@patch('app.api.routes.ingest_tabular.create_engine_from_dsn')
def test_ingest_tabular_failure(mock_create_engine, client):
    """Test API error handling when ingestion fails."""
    # Mock engine creation to raise an exception
    mock_create_engine.side_effect = Exception("Database connection failed")
    
    # Make API request
    response = client.post("/v1/ingest/csv", json={
        "dsn": "postgresql://bad:connection@localhost:5432/testdb",
        "customers_csv_path": "data/fake_customers.csv"
    })
    
    # Check error response
    assert response.status_code == 400
    data = response.json()
    assert "Ingestion failed" in data["detail"]
    assert "Database connection failed" in data["detail"]


def test_ingest_tabular_missing_dsn(client):
    """Test that DSN is required."""
    response = client.post("/v1/ingest/csv", json={
        "customers_csv_path": "data/fake_customers.csv"
    })
    
    # Should get validation error for missing required field
    assert response.status_code == 422


def test_ingest_tabular_optional_paths(client):
    """Test that CSV paths are optional."""
    with patch('app.api.routes.ingest_tabular.create_engine_from_dsn') as mock_create, \
         patch('app.api.routes.ingest_tabular.load_csvs') as mock_load, \
         patch('app.api.routes.ingest_tabular.close_engine') as mock_close:
        
        mock_engine = AsyncMock()
        mock_create.return_value = mock_engine
        mock_load.return_value = 0
        mock_close.return_value = None
        
        # Request with only DSN (no CSV paths)
        response = client.post("/v1/ingest/csv", json={
            "dsn": "postgresql://user:pass@localhost:5432/testdb"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # load_csvs should be called with None for all CSV paths
        mock_load.assert_called_once_with(mock_engine, None, None, None)

