from typing import Literal, Optional

from pydantic import BaseModel, Field

ColorLabel = Literal["gray", "red", "orange", "yellow", "green", "blue", "purple"]


class Board(BaseModel):
    id: str
    name: str
    created_at: str


class BoardCreate(BaseModel):
    name: str = Field(min_length=1)


class BoardUpdate(BaseModel):
    name: str = Field(min_length=1)


class Column(BaseModel):
    id: str
    board_id: str
    name: str
    position: int


class ColumnCreate(BaseModel):
    name: str = Field(min_length=1)


class ColumnUpdate(BaseModel):
    name: str = Field(min_length=1)


class ColumnReorder(BaseModel):
    ordered_ids: list[str]


class Card(BaseModel):
    id: str
    column_id: str
    title: str
    description: Optional[str] = None
    color_label: Optional[ColorLabel] = None
    position: int


class CardCreate(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = None
    color_label: Optional[ColorLabel] = None


class CardUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    color_label: Optional[ColorLabel] = None


class CardMove(BaseModel):
    target_column_id: str
    target_position: int = Field(ge=0)


class BoardDetail(BaseModel):
    board: Board
    columns: list[Column]
    cards: list[Card]
