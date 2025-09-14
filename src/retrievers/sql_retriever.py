from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text


class SQLRetriever:
    """Parameterized SQL retriever for common ecommerce intents."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def get_order_status(self, order_id: int) -> Optional[Dict[str, Any]]:
        q = text(
            """
            SELECT order_id, order_status, order_date FROM orders WHERE order_id = :order_id
            """
        )
        async with self.engine.connect() as conn:
            res = await conn.execute(q, {"order_id": order_id})
            row = res.mappings().first()
            return dict(row) if row else None


