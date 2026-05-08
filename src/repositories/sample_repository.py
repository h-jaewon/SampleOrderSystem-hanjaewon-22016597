import sqlite3
from pathlib import Path
from typing import Optional

from src.models.sample import Sample


class SampleRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            import src.database as _database
            db_path = _database.DB_PATH
        self._db_path = db_path

        from src.database import init_db
        init_db(self._db_path)

    def add(self, sample: Sample) -> None:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            with conn:
                conn.execute(
                    "INSERT INTO samples (id, name, avg_production_time, yield_, stock) VALUES (?, ?, ?, ?, ?)",
                    (sample.id, sample.name, sample.avgProductionTime, sample.yield_, sample.stock),
                )
        except sqlite3.IntegrityError:
            raise ValueError(f"이미 존재하는 시료 ID입니다: {sample.id}")
        finally:
            conn.close()

    def get(self, sample_id: str) -> Optional[Sample]:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            row = conn.execute("SELECT * FROM samples WHERE id = ?", (sample_id,)).fetchone()
        finally:
            conn.close()
        return self._row_to_sample(row) if row else None

    def get_all(self) -> list[Sample]:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            rows = conn.execute("SELECT * FROM samples ORDER BY id").fetchall()
        finally:
            conn.close()
        return [self._row_to_sample(row) for row in rows]

    def find_by_name(self, name: str) -> list[Sample]:
        keyword = name.lower()
        return [s for s in self.get_all() if keyword in s.name.lower()]

    def update_stock(self, sample_id: str, stock: int) -> None:
        from src.database import get_connection
        conn = get_connection(self._db_path)
        try:
            with conn:
                conn.execute("UPDATE samples SET stock = ? WHERE id = ?", (stock, sample_id))
        finally:
            conn.close()

    @staticmethod
    def _row_to_sample(row: sqlite3.Row) -> Sample:
        return Sample(
            id=row["id"],
            name=row["name"],
            avgProductionTime=row["avg_production_time"],
            yield_=row["yield_"],
            stock=row["stock"],
        )
