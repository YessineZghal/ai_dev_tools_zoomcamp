"""Database engine/session setup.

DATABASE_URL controls which database is used, keeping the app
database-agnostic — swap the URL to point at a different SQLAlchemy-
supported database without touching any other file.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./flowboard.db")

# check_same_thread is only needed/valid for SQLite.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
