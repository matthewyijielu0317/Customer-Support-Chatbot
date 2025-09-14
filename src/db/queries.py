from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text


async def get_order_by_id(engine: AsyncEngine, order_id: int) -> Optional[Dict[str, Any]]:
    q = text("SELECT * FROM orders WHERE order_id = :oid")
    async with engine.connect() as conn:
        res = await conn.execute(q, {"oid": order_id})
        row = res.mappings().first()
        return dict(row) if row else None


