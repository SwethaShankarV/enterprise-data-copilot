from sqlalchemy import create_engine, text
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("DB_PATH") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "enterprise.db"))
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

# Simple safety check: reject destructive/DDL keywords (trailing space to avoid "deleted" etc.)
_SQL_BLACKLIST = ["drop ", "alter ", "attach ", "detach ", "update ", "delete ", "insert ", "truncate "]

def run_sql_query(query: str):
    q = (query or "").strip().lower()
    if any(b in q for b in _SQL_BLACKLIST):
        return {"error": "Query rejected by safety policy."}
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            columns = result.keys()
        logger.info("Executed SQL: %s; rows=%d", query, len(rows))
        return {
            "columns": list(columns),
            "rows": [list(row) for row in rows]
        }
    except Exception as e:
        logger.exception("SQL execution failed")
        return {"error": str(e)}