import re
from typing import List, Dict, Any

from src.config.settings import settings
from copy import deepcopy
from src.persistence.postgres import create_sync_engine, get_order_for_user
from src.graph.state import RAGState, Citation
from src.utils.masking import mask_email


_ENGINE = create_sync_engine(settings.postgres_dsn) if settings.postgres_dsn else None


def _extract_entities(user_query: str) -> Dict[str, Any]:
    query = (user_query or "").strip()
    out: Dict[str, Any] = {}

    # order id: accept "order 123", "order #123", "#123", or standalone digits
    m_order = re.search(r"order\s*(?:number|#)?\s*(\d{1,6})", query, flags=re.I)
    if not m_order:
        m_order = re.search(r"#(\d{1,6})\b", query)
    if not m_order:
        stripped = query.replace(" ", "")
        if re.fullmatch(r"#?(\d{1,6})", stripped):
            m_order = re.search(r"(\d{1,6})", stripped)

    if m_order:
        try:
            out["order_id"] = int(m_order.group(1))
        except ValueError:
            pass

    return out


def _rows_to_citations(rows: List[Dict[str, Any]]) -> List[Citation]:
    cites: List[Citation] = []
    for r in rows:
        if "order_id" in r:
            cites.append(Citation(source=f"db:orders#{r['order_id']}", title="orders"))
    return cites


def _mask_row(row: Dict[str, Any], query: str) -> Dict[str, Any]:
    masked = deepcopy(row)
    if "customer_email" in masked:
        masked["customer_email"] = mask_email(masked.get("customer_email"), query)
    if "email" in masked:
        masked["email"] = mask_email(masked.get("email"), query)
    return masked


def retrieve_sql_node(state: RAGState) -> RAGState:
    if not state.should_retrieve_sql:
        state.sql_rows = []
        return state

    # If DSN not configured or engine missing, skip
    if _ENGINE is None or not settings.postgres_dsn:
        state.sql_rows = []
        return state

    user_id = state.user_id
    if not user_id:
        state.sql_rows = []
        return state

    entities = _extract_entities(state.query)
    if state.order_id is None and entities.get("order_id") is not None:
        try:
            state.order_id = int(entities["order_id"])
        except (TypeError, ValueError):
            state.order_id = None

    sql_rows: List[Dict[str, Any]] = []

    if state.order_id is not None:
        od = get_order_for_user(_ENGINE, user_id, int(state.order_id))
        if od:
            masked = _mask_row(od, state.query)
            sql_rows.append(masked)
            if not state.first_name and masked.get("first_name"):
                state.first_name = str(masked.get("first_name"))
            if not state.last_name and masked.get("last_name"):
                state.last_name = str(masked.get("last_name"))

    state.sql_rows = sql_rows

    # Attach db citations (keep existing citations from doc retrieval intact)
    if sql_rows:
        db_cites = _rows_to_citations(sql_rows)
        state.citations = (state.citations or []) + db_cites

    return state
