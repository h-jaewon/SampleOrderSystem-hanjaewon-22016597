import sqlite3
from pathlib import Path
from typing import Optional

from src.models.production_job import ProductionJob


class ProductionQueue:
    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            import src.database as _database
            db_path = _database.DB_PATH
        self._db_path = db_path

        from src.database import init_db
        init_db(self._db_path)

    def enqueue(self, job: ProductionJob) -> None:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            with conn:
                conn.execute(
                    "INSERT INTO production_queue (order_id, sample_id, planned_quantity, total_production_time) VALUES (?, ?, ?, ?)",
                    (job.orderId, job.sampleId, job.plannedQuantity, job.totalProductionTime),
                )
        finally:
            conn.close()

    def dequeue(self) -> ProductionJob:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            with conn:
                row = conn.execute(
                    "SELECT * FROM production_queue ORDER BY seq LIMIT 1"
                ).fetchone()
                if row is None:
                    raise IndexError("생산 큐가 비어있습니다.")
                conn.execute("DELETE FROM production_queue WHERE seq = ?", (row["seq"],))
        finally:
            conn.close()
        return self._row_to_job(row)

    def peek(self) -> Optional[ProductionJob]:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            row = conn.execute(
                "SELECT * FROM production_queue ORDER BY seq LIMIT 1"
            ).fetchone()
        finally:
            conn.close()
        return self._row_to_job(row) if row else None

    def get_all(self) -> list[ProductionJob]:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            rows = conn.execute("SELECT * FROM production_queue ORDER BY seq").fetchall()
        finally:
            conn.close()
        return [self._row_to_job(row) for row in rows]

    def is_empty(self) -> bool:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM production_queue").fetchone()[0]
        finally:
            conn.close()
        return count == 0

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> ProductionJob:
        return ProductionJob(
            orderId=row["order_id"],
            sampleId=row["sample_id"],
            plannedQuantity=row["planned_quantity"],
            totalProductionTime=row["total_production_time"],
        )
