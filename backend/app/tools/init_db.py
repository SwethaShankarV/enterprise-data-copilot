from sqlalchemy import create_engine, text
import os

DB_PATH = os.environ.get("DB_PATH") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "enterprise.db"))
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY,
            region TEXT,
            product TEXT,
            revenue FLOAT,
            order_date TEXT
        )
        """))

        # Insert only if table empty (idempotent)
        result = conn.execute(text("SELECT COUNT(1) as c FROM sales"))
        count = result.fetchone().c
        if count == 0:
            conn.execute(text("""
            INSERT INTO sales (region, product, revenue, order_date) VALUES
            ('West', 'Laptop', 12000, '2025-01-10'),
            ('West', 'Phone', 8000, '2025-01-15'),
            ('East', 'Laptop', 15000, '2025-01-20'),
            ('East', 'Phone', 5000, '2025-01-25'),
            ('West', 'Tablet', 4000, '2025-02-01')
            """))

if __name__ == "__main__":
    init_db()
    print(f"DB initialized at {DB_PATH}")