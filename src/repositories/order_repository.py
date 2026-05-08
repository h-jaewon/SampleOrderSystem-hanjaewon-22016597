import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.database import connect, init_db
from src.models.order import Order, OrderStatus


class OrderRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            import src.database as _database
            db_path = _database.DB_PATH
        self._db_path = db_path
        init_db(self._db_path)

    def add(self, order: Order) -> None:
        try:
            with connect(self._db_path) as conn:
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

    def get(self, order_id: str) -> Optional[Order]:
        with connect(self._db_path) as conn:
            row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        return self._row_to_order(row) if row else None

    def get_all(self) -> list[Order]:
        with connect(self._db_path) as conn:
            rows = conn.execute("SELECT * FROM orders ORDER BY id").fetchall()
        return [self._row_to_order(row) for row in rows]

    def get_by_status(self, status: OrderStatus) -> list[Order]:
        with connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM orders WHERE status = ? ORDER BY id", (status.value,)
            ).fetchall()
        return [self._row_to_order(row) for row in rows]

    def update_status(self, order_id: str, status: OrderStatus) -> None:
        with connect(self._db_path) as conn:
            with conn:
                conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status.value, order_id))

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
