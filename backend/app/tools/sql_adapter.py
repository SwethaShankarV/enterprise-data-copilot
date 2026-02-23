# backend/app/tools/sql_adapter.py
import os
import logging
from app.tools.sql_tool import run_sql_query as run_sql_local

logger = logging.getLogger(__name__)

# ENV: sqlite (default) or fabric / azure_sql / azure_synapse
DEFAULT_SQL_SOURCE = os.getenv("SQL_SOURCE", "sqlite").lower()
FABRIC_CONN = os.getenv("FABRIC_CONN_STRING")


def run_sql_query(query: str, source: str = None):
    """
    Unified adapter: local sqlite or Fabric/Azure SQL.
    - source: 'sqlite' (default) or 'fabric' / 'azure_sql' / 'azure_synapse'
    """
    src = (source or DEFAULT_SQL_SOURCE).lower()

    if src == "sqlite":
        return run_sql_local(query)

    if src in ("fabric", "azure_sql", "azure_synapse"):
        if not FABRIC_CONN:
            return {"error": "FABRIC_CONN_STRING not set; cannot query Fabric."}
        # Placeholder: implement with pyodbc/sqlalchemy + FABRIC_CONN
        # Return {"columns": [...], "rows": [[...]]} or {"error": "..."}
        return {"error": "Fabric connector not implemented. See app/tools/sql_adapter.py."}

    return {"error": f"Unknown SQL source: {src}"}
