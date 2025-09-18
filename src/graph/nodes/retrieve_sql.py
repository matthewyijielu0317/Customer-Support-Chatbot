import re
from typing import List, Dict, Any

from src.config.settings import settings
from src.db.postgres_sync import create_engine_sync
from src.db import queries as q
from src.graph.state import RAGState, Citation


_ENGINE = create_engine_sync(settings.postgres_dsn) if settings.postgres_dsn else None


def _extract_entities(user_query: str) -> Dict[str, Any]:
    query = (user_query or "").strip()
    out: Dict[str, Any] = {}

    # email
    m_email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", query)
    if m_email:
        out["customer_email"] = m_email.group(0)

    # order id: first standalone integer up to 6 digits when 'order' is referenced
    if re.search(r"order", query, flags=re.I):
        m_num = re.search(r"\b(\d{1,6})\b", query)
        if m_num:
            try:
                out["order_id"] = int(m_num.group(1))
            except ValueError:
                pass

    # product id: integer following 'product'
    m_prod = re.search(r"product\s*#?\s*(\d{1,6})", query, flags=re.I)
    if m_prod:
        try:
            out["product_id"] = int(m_prod.group(1))
        except ValueError:
            pass

    return out


def _rows_to_citations(rows: List[Dict[str, Any]]) -> List[Citation]:
    cites: List[Citation] = []
    for r in rows:
        if "order_id" in r:
            cites.append(Citation(source=f"db:orders#{r['order_id']}", title="orders"))
        elif "product_id" in r:
            cites.append(Citation(source=f"db:products#{r['product_id']}", title="products"))
        elif "customer_id" in r:
            cites.append(Citation(source=f"db:customers#{r['customer_id']}", title="customers"))
    return cites


def retrieve_sql_node(state: RAGState) -> RAGState:
    # If DSN not configured or engine missing, skip
    if _ENGINE is None or not settings.postgres_dsn:
        state.sql_rows = []
        return state

    entities = _extract_entities(state.query)
    state.entities.update(entities)

    sql_rows: List[Dict[str, Any]] = []

    # Priority: order -> email -> product
    if "order_id" in entities:
        od = q.get_order_details_by_id(_ENGINE, int(entities["order_id"]))
        if od:
            sql_rows.append(od)
    elif "customer_email" in entities:
        recent = q.get_recent_orders_by_email(_ENGINE, str(entities["customer_email"]))
        sql_rows.extend(recent)
        cust = q.get_customer_by_email(_ENGINE, str(entities["customer_email"]))
        if cust:
            sql_rows.insert(0, cust)
    elif "product_id" in entities:
        pd = q.get_product_by_id(_ENGINE, int(entities["product_id"]))
        if pd:
            sql_rows.append(pd)

    state.sql_rows = sql_rows

    # Attach db citations (keep existing citations from doc retrieval intact)
    if sql_rows:
        db_cites = _rows_to_citations(sql_rows)
        state.citations = (state.citations or []) + db_cites

    return state


