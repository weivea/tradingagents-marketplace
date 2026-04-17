import sqlite3
import pytest
from python.db import init_schema


@pytest.fixture
def conn():
    """Fresh in-memory SQLite with schema initialized."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    init_schema(c)
    yield c
    c.close()
