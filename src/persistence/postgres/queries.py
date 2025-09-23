"""PostgreSQL query functions for customer support operations."""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine


def get_order_for_user(engine: Engine, user_id: str, order_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single order for the authenticated user, including product metadata.
    
    Args:
        engine: SQLAlchemy engine
        user_id: User identifier (email)
        order_id: Order ID to fetch
        
    Returns:
        Order details with customer and product info, or None if not found
    """
    statement = text(
        """
        SELECT
            o.*, p.product_name, p.product_category, p.unit_price, 
            c.customer_id, c.email AS customer_email, c.first_name, c.last_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN products p ON o.product_id = p.product_id
        WHERE c.user_id = :user_id AND o.order_id = :order_id
        LIMIT 1
        """
    )

    with engine.connect() as conn:
        row = conn.execute(
            statement,
            {"user_id": user_id, "order_id": order_id},
        ).mappings().first()

    return dict(row) if row else None
