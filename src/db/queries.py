from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine


def get_order_details_by_id(engine: Engine, order_id: int) -> Optional[Dict[str, Any]]:
    """Return one order with joined customer and product details."""
    q = text(
        """
        SELECT o.*, c.email AS customer_email, c.first_name, c.last_name,
               p.product_name, p.product_category, p.unit_price
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN products p ON o.product_id = p.product_id
        WHERE o.order_id = :oid
        """
    )
    with engine.connect() as conn:
        res = conn.execute(q, {"oid": order_id})
        row = res.mappings().first()
        return dict(row) if row else None


def get_customer_by_email(engine: Engine, email: str) -> Optional[Dict[str, Any]]:
    q = text("SELECT * FROM customers WHERE email = :email LIMIT 1")
    with engine.connect() as conn:
        res = conn.execute(q, {"email": email})
        row = res.mappings().first()
        return dict(row) if row else None


def get_recent_orders_by_email(engine: Engine, email: str, limit: int = 5) -> List[Dict[str, Any]]:
    q = text(
        """
        SELECT o.*, p.product_name, p.product_category, p.unit_price
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN products p ON o.product_id = p.product_id
        WHERE c.email = :email
        ORDER BY o.order_date DESC
        LIMIT :limit
        """
    )
    with engine.connect() as conn:
        res = conn.execute(q, {"email": email, "limit": limit})
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

