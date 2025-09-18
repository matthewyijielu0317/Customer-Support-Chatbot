from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from typing import Iterable, List, Optional

from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection, create_async_engine


CUSTOMER_COLUMNS = ["customer_id", "first_name", "last_name", "email", "gender", "user_id", "passcode"]
ORDER_COLUMNS = ["order_id", "customer_id", "product_id", "quantity", "order_date", "delivery_date"]
PRODUCT_COLUMNS = ["product_id", "product_name", "product_category", "unit_price"]


CUSTOMER_COERCIONS = {
    "customer_id": int,
}

def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


ORDER_COERCIONS = {
    "order_id": int,
    "customer_id": int,
    "product_id": int,
    "quantity": int,
    "order_date": _parse_date,
    "delivery_date": _parse_date,
}

PRODUCT_COERCIONS = {
    "product_id": int,
    "unit_price": float,
}


def create_engine_from_dsn(dsn: str) -> AsyncEngine:
    if not dsn:
        raise ValueError("Postgres DSN is required")
    if "+asyncpg" not in dsn:
        if dsn.startswith("postgresql://"):
            dsn = dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif dsn.startswith("postgres://"):
            dsn = dsn.replace("postgres://", "postgresql+asyncpg://", 1)
        else:
            dsn = f"postgresql+asyncpg://{dsn}"
    return create_async_engine(dsn, echo=False, future=True)


async def load_csvs(
    engine: AsyncEngine,
    customers_path: Optional[str] = None,
    orders_path: Optional[str] = None,
    products_path: Optional[str] = None,
) -> int:
    total_rows = 0
    async with engine.begin() as conn:
        await _ensure_schema(conn)
        if customers_path:
            total_rows += await _load_customers(conn, customers_path)
        if products_path:
            total_rows += await _load_products(conn, products_path)
        if orders_path:
            total_rows += await _load_orders(conn, orders_path)
    return total_rows


async def _ensure_schema(conn: AsyncConnection) -> None:
    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                gender TEXT,
                user_id TEXT,
                passcode TEXT
            )
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT,
                product_category TEXT,
                unit_price NUMERIC
            )
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER REFERENCES customers(customer_id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(product_id) ON DELETE CASCADE,
                quantity INTEGER,
                order_date DATE,
                delivery_date DATE
            )
            """
        )
    )


async def _load_customers(conn: AsyncConnection, path: str) -> int:
    rows = _read_csv(path, CUSTOMER_COERCIONS)
    if not rows:
        return 0

    for row in rows:
        row.setdefault("user_id", row.get("email"))
        if not row.get("user_id"):
            row["user_id"] = row.get("email") or f"customer-{row.get('customer_id')}"
        row.setdefault("passcode", "12345")

    await conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS user_id TEXT"))
    await conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS passcode TEXT"))
    await conn.execute(text("TRUNCATE TABLE customers RESTART IDENTITY CASCADE"))

    insert = text(
        """
        INSERT INTO customers (customer_id, first_name, last_name, email, gender, user_id, passcode)
        VALUES (:customer_id, :first_name, :last_name, :email, :gender, :user_id, :passcode)
        """
    )
    await conn.execute(insert, rows)
    return len(rows)


async def _load_orders(conn: AsyncConnection, path: str) -> int:
    rows = _read_csv(path, ORDER_COERCIONS)
    if not rows:
        return 0

    await conn.execute(text("TRUNCATE TABLE orders RESTART IDENTITY CASCADE"))
    insert = text(
        """
        INSERT INTO orders (order_id, customer_id, product_id, quantity, order_date, delivery_date)
        VALUES (:order_id, :customer_id, :product_id, :quantity, :order_date, :delivery_date)
        """
    )
    await conn.execute(insert, rows)
    return len(rows)


async def _load_products(conn: AsyncConnection, path: str) -> int:
    rows = _read_csv(path, PRODUCT_COERCIONS)
    if not rows:
        return 0

    await conn.execute(text("TRUNCATE TABLE products RESTART IDENTITY CASCADE"))
    insert = text(
        """
        INSERT INTO products (product_id, product_name, product_category, unit_price)
        VALUES (:product_id, :product_name, :product_category, :unit_price)
        """
    )
    await conn.execute(insert, rows)
    return len(rows)


def _read_csv(path: str, coercions: Optional[dict[str, callable]] = None) -> List[dict]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with file_path.open("r", newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        rows = []
        for row in reader:
            if coercions:
                for key, caster in coercions.items():
                    if key in row and row[key] not in (None, ""):
                        row[key] = caster(row[key])
            rows.append(row)
    return rows


async def close_engine(engine: AsyncEngine) -> None:
    await engine.dispose()
