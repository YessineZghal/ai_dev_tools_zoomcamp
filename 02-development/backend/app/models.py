"""SQLAlchemy ORM models for Board, Column, Card.

Plain columns and relationships only — no database-specific types — so
this schema works the same on SQLite or any other SQLAlchemy-supported
database.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column as SAColumn
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base


def _new_id() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class BoardModel(Base):
    __tablename__ = "boards"

    id = SAColumn(String, primary_key=True, default=_new_id)
    name = SAColumn(String, nullable=False)
    created_at = SAColumn(DateTime(timezone=True), default=_now)

    columns = relationship(
        "ColumnModel", cascade="all, delete-orphan", back_populates="board"
    )


class ColumnModel(Base):
    __tablename__ = "columns"

    id = SAColumn(String, primary_key=True, default=_new_id)
    board_id = SAColumn(String, ForeignKey("boards.id"), nullable=False)
    name = SAColumn(String, nullable=False)
    position = SAColumn(Integer, nullable=False, default=0)

    board = relationship("BoardModel", back_populates="columns")
    cards = relationship(
        "CardModel", cascade="all, delete-orphan", back_populates="column"
    )


class CardModel(Base):
    __tablename__ = "cards"

    id = SAColumn(String, primary_key=True, default=_new_id)
    column_id = SAColumn(String, ForeignKey("columns.id"), nullable=False)
    title = SAColumn(String, nullable=False)
    description = SAColumn(String, nullable=True)
    color_label = SAColumn(String, nullable=True)
    position = SAColumn(Integer, nullable=False, default=0)

    column = relationship("ColumnModel", back_populates="cards")
