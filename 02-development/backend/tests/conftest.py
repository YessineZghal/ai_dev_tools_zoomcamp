import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.main as main_module
from app.db import Base
from app.sql_store import SqlStore


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """Give every test a fresh, isolated in-memory SQLite database.

    StaticPool is required here: an in-memory SQLite database only exists
    for the lifetime of a single connection, and FastAPI runs sync route
    handlers in a worker thread, so without a shared/static connection
    each request could see an empty database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(main_module, "store", SqlStore(test_session_factory))
    yield
