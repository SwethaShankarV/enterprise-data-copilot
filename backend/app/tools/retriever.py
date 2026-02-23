# backend/app/tools/retriever.py
import os
import json
import logging

logger = logging.getLogger(__name__)

METRICS_PATH = os.getenv(
    "METRICS_JSON",
    os.path.join(os.path.dirname(__file__), "metrics.json"),
)


def load_local_metrics():
    try:
        with open(METRICS_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        default = {
            "total_revenue": "Sum of revenue across orders. SQL: SELECT SUM(revenue) AS total_revenue FROM sales WHERE {filters};",
            "revenue_by_product": "Total revenue grouped by product. SQL: SELECT product, SUM(revenue) AS total_revenue FROM sales {filters} GROUP BY product;",
        }
        try:
            with open(METRICS_PATH, "w") as f:
                json.dump(default, f, indent=2)
        except OSError:
            logger.warning("Could not write default metrics.json at %s", METRICS_PATH)
        return default


def retrieve_relevant_docs(query: str, top_k: int = 5):
    """
    Retrieval for RAG: local metrics.json now; later swap for Azure Cognitive Search / vector DB.
    """
    metrics = load_local_metrics()
    results = []
    q = (query or "").lower()
    for k, v in metrics.items():
        if any(tok in q for tok in k.split("_")) or any(tok in q for tok in (v or "").lower().split()):
            results.append({"id": k, "text": v})
    if not results:
        for k, v in metrics.items():
            results.append({"id": k, "text": v})
    return results[:top_k]
