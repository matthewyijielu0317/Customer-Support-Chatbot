from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine


def get_customer_by_user_id(engine: Engine, user_id: str) -> Optional[Dict[str, Any]]:
    q = text("SELECT * FROM customers WHERE user_id = :user_id LIMIT 1")
    with engine.connect() as conn:
        row = conn.execute(q, {"user_id": user_id}).mappings().first()
        return dict(row) if row else None


def get_order_details_for_user(engine: Engine, user_id: str, order_id: int) -> Optional[Dict[str, Any]]:
    """Return an order only if it belongs to the authenticated user."""
    q = text(
        """
        SELECT o.*, c.email AS customer_email, c.first_name, c.last_name,
               p.product_name, p.product_category, p.unit_price
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN products p ON o.product_id = p.product_id
        WHERE o.order_id = :oid AND c.user_id = :user_id
        """
    )
    with engine.connect() as conn:
        res = conn.execute(q, {"oid": order_id, "user_id": user_id})
        row = res.mappings().first()
        return dict(row) if row else None


def get_customer_profile(engine: Engine, user_id: str) -> Optional[Dict[str, Any]]:
    q = text(
        """
        SELECT customer_id, first_name, last_name, email, gender
        FROM customers
        WHERE user_id = :user_id
        LIMIT 1
        """
    )
    with engine.connect() as conn:
        res = conn.execute(q, {"user_id": user_id})
        row = res.mappings().first()
        return dict(row) if row else None


def get_recent_orders_for_user(engine: Engine, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    q = text(
        """
        SELECT o.*, p.product_name, p.product_category, p.unit_price
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN products p ON o.product_id = p.product_id
        WHERE c.user_id = :user_id
        ORDER BY o.order_date DESC
        LIMIT :limit
        """
    )
    with engine.connect() as conn:
        res = conn.execute(q, {"user_id": user_id, "limit": limit})
        return [dict(r) for r in res.mappings().all()]


def get_product_by_id(engine: Engine, product_id: int) -> Optional[Dict[str, Any]]:
    q = text("SELECT * FROM products WHERE product_id = :pid")
    with engine.connect() as conn:
        res = conn.execute(q, {"pid": product_id})
        row = res.mappings().first()
        return dict(row) if row else None


def search_products_by_name(engine: Engine, name_query: str, limit: int = 5) -> List[Dict[str, Any]]:
    q = text("SELECT * FROM products WHERE product_name ILIKE :q LIMIT :limit")
    with engine.connect() as conn:
        res = conn.execute(q, {"q": f"%{name_query}%", "limit": limit})
        return [dict(r) for r in res.mappings().all()]
