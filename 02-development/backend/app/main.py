from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, SessionLocal, engine
from app.schemas import (
    Board,
    BoardCreate,
    BoardDetail,
    BoardUpdate,
    Card,
    CardCreate,
    CardMove,
    CardUpdate,
    Column,
    ColumnCreate,
    ColumnReorder,
    ColumnUpdate,
)
from app.sql_store import SqlStore

app = FastAPI(title="Flowboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(engine)
store = SqlStore(SessionLocal)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/boards", response_model=list[Board])
def list_boards():
    return store.list_boards()


@app.post("/boards", response_model=Board, status_code=201)
def create_board(payload: BoardCreate):
    return store.create_board(payload.name)


@app.get("/boards/{board_id}", response_model=BoardDetail)
def get_board(board_id: str):
    board = store.get_board(board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return BoardDetail(
        board=board,
        columns=store.list_columns(board_id),
        cards=store.list_cards_for_board(board_id),
    )


@app.patch("/boards/{board_id}", response_model=Board)
def rename_board(board_id: str, payload: BoardUpdate):
    board = store.rename_board(board_id, payload.name)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@app.delete("/boards/{board_id}", status_code=204)
def delete_board(board_id: str):
    if not store.delete_board(board_id):
        raise HTTPException(status_code=404, detail="Board not found")


@app.post("/boards/{board_id}/columns", response_model=Column, status_code=201)
def create_column(board_id: str, payload: ColumnCreate):
    if store.get_board(board_id) is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return store.create_column(board_id, payload.name)


@app.patch("/columns/{column_id}", response_model=Column)
def rename_column(column_id: str, payload: ColumnUpdate):
    column = store.rename_column(column_id, payload.name)
    if column is None:
        raise HTTPException(status_code=404, detail="Column not found")
    return column


@app.delete("/columns/{column_id}", status_code=204)
def delete_column(column_id: str):
    if not store.delete_column(column_id):
        raise HTTPException(status_code=404, detail="Column not found")


@app.patch("/columns/{column_id}/reorder", response_model=list[Column])
def reorder_columns(column_id: str, payload: ColumnReorder):
    column = store.get_column(column_id)
    if column is None:
        raise HTTPException(status_code=404, detail="Column not found")
    return store.reorder_columns(column.board_id, payload.ordered_ids)


@app.post("/columns/{column_id}/cards", response_model=Card, status_code=201)
def create_card(column_id: str, payload: CardCreate):
    if store.get_column(column_id) is None:
        raise HTTPException(status_code=404, detail="Column not found")
    return store.create_card(column_id, payload.title, payload.description, payload.color_label)


@app.patch("/cards/{card_id}", response_model=Card)
def update_card(card_id: str, payload: CardUpdate):
    card = store.update_card(card_id, **payload.model_dump(exclude_unset=True))
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


@app.delete("/cards/{card_id}", status_code=204)
def delete_card(card_id: str):
    if not store.delete_card(card_id):
        raise HTTPException(status_code=404, detail="Card not found")


@app.patch("/cards/{card_id}/move", response_model=Card)
def move_card(card_id: str, payload: CardMove):
    card = store.move_card(card_id, payload.target_column_id, payload.target_position)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return card
