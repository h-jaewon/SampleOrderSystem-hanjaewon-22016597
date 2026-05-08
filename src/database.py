import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "sampleordersystem.db"


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connect(db_path: Path):
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Path) -> None:
    with get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS samples (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                avg_production_time REAL NOT NULL,
                yield_ REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                sample_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS production_queue (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                sample_id TEXT NOT NULL,
                planned_quantity INTEGER NOT NULL,
                total_production_time REAL NOT NULL
            )
        """)
