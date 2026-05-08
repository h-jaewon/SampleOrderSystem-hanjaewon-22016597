import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.order import Order, OrderStatus


class OrderRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            import src.database as _database
            db_path = _database.DB_PATH
        self._db_path = db_path

        from src.database import init_db
        init_db(self._db_path)

    def add(self, order: Order) -> None:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            with conn:
                conn.execute(
                    "INSERT INTO orders (id, sample_id, customer_name, quantity, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        order.id,
                        order.sampleId,
                        order.customerName,
                        order.quantity,
                        order.status.value,
                        order.createdAt.isoformat(),
                    ),
                )
        except sqlite3.IntegrityError:
            raise ValueError(f"이미 존재하는 주문 ID입니다: {order.id}")
        finally:
            conn.close()

    def get(self, order_id: str) -> Optional[Order]:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        finally:
            conn.close()
        return self._row_to_order(row) if row else None

    def get_all(self) -> list[Order]:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            rows = conn.execute("SELECT * FROM orders ORDER BY id").fetchall()
        finally:
            conn.close()
        return [self._row_to_order(row) for row in rows]

    def get_by_status(self, status: OrderStatus) -> list[Order]:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM orders WHERE status = ? ORDER BY id", (status.value,)
            ).fetchall()
        finally:
            conn.close()
        return [self._row_to_order(row) for row in rows]

    def update_status(self, order_id: str, status: OrderStatus) -> None:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            with conn:
                conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status.value, order_id))
        finally:
            conn.close()

    @staticmethod
    def _row_to_order(row: sqlite3.Row) -> Order:
        return Order(
            id=row["id"],
            sampleId=row["sample_id"],
            customerName=row["customer_name"],
            quantity=row["quantity"],
            status=OrderStatus(row["status"]),
            createdAt=datetime.fromisoformat(row["created_at"]),
        )
