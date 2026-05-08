import pytest
from pathlib import Path
import src.database as _db


@pytest.fixture
def db_path(tmp_path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture(autouse=True)
def _isolated_db(db_path, monkeypatch):
    monkeypatch.setattr(_db, "DB_PATH", db_path)
