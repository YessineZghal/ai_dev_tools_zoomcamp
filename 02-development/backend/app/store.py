"""In-memory implementation of the Flowboard data store.

This is the mock backend called for by the homework: it satisfies the same
interface a SQLAlchemy-backed store implements later, so route handlers in
app/main.py never change when the storage layer does.
"""

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import Board, Card, Column


def _new_id() -> str:
    return uuid4().hex


class Store:
    def __init__(self) -> None:
        self._boards: dict[str, Board] = {}
        self._columns: dict[str, Column] = {}
        self._cards: dict[str, Card] = {}

    # --- Boards ---

    def list_boards(self) -> list[Board]:
        return list(self._boards.values())

    def create_board(self, name: str) -> Board:
        board = Board(id=_new_id(), name=name, created_at=datetime.now(timezone.utc).isoformat())
        self._boards[board.id] = board
        return board

    def get_board(self, board_id: str) -> Board | None:
        return self._boards.get(board_id)

    def rename_board(self, board_id: str, name: str) -> Board | None:
        board = self._boards.get(board_id)
        if board is None:
            return None
        updated = board.model_copy(update={"name": name})
        self._boards[board_id] = updated
        return updated

    def delete_board(self, board_id: str) -> bool:
        if board_id not in self._boards:
            return False
        column_ids = [c.id for c in self._columns.values() if c.board_id == board_id]
        for column_id in column_ids:
            self.delete_column(column_id)
        del self._boards[board_id]
        return True

    # --- Columns ---

    def list_columns(self, board_id: str) -> list[Column]:
        return sorted(
            (c for c in self._columns.values() if c.board_id == board_id),
            key=lambda c: c.position,
        )

    def list_cards_for_board(self, board_id: str) -> list[Card]:
        column_ids = {c.id for c in self._columns.values() if c.board_id == board_id}
        return [card for card in self._cards.values() if card.column_id in column_ids]

    def get_column(self, column_id: str) -> Column | None:
        return self._columns.get(column_id)

    def create_column(self, board_id: str, name: str) -> Column:
        position = len(self.list_columns(board_id))
        column = Column(id=_new_id(), board_id=board_id, name=name, position=position)
        self._columns[column.id] = column
        return column

    def rename_column(self, column_id: str, name: str) -> Column | None:
        column = self._columns.get(column_id)
        if column is None:
            return None
        updated = column.model_copy(update={"name": name})
        self._columns[column_id] = updated
        return updated

    def delete_column(self, column_id: str) -> bool:
        if column_id not in self._columns:
            return False
        card_ids = [k.id for k in self._cards.values() if k.column_id == column_id]
        for card_id in card_ids:
            del self._cards[card_id]
        del self._columns[column_id]
        return True

    def reorder_columns(self, board_id: str, ordered_ids: list[str]) -> list[Column]:
        for index, column_id in enumerate(ordered_ids):
            column = self._columns.get(column_id)
            if column is not None:
                self._columns[column_id] = column.model_copy(update={"position": index})
        return self.list_columns(board_id)

    # --- Cards ---

    def _sorted_cards_in(self, column_id: str, exclude_id: str | None = None) -> list[Card]:
        cards = [
            c
            for c in self._cards.values()
            if c.column_id == column_id and c.id != exclude_id
        ]
        return sorted(cards, key=lambda c: c.position)

    def create_card(
        self,
        column_id: str,
        title: str,
        description: str | None,
        color_label: str | None,
    ) -> Card:
        position = len(self._sorted_cards_in(column_id))
        card = Card(
            id=_new_id(),
            column_id=column_id,
            title=title,
            description=description,
            color_label=color_label,
            position=position,
        )
        self._cards[card.id] = card
        return card

    def update_card(self, card_id: str, **fields) -> Card | None:
        card = self._cards.get(card_id)
        if card is None:
            return None
        updated = card.model_copy(update=fields)
        self._cards[card_id] = updated
        return updated

    def delete_card(self, card_id: str) -> bool:
        if card_id not in self._cards:
            return False
        del self._cards[card_id]
        return True

    def move_card(self, card_id: str, target_column_id: str, target_position: int) -> Card | None:
        card = self._cards.get(card_id)
        if card is None:
            return None

        target_siblings = self._sorted_cards_in(target_column_id, exclude_id=card_id)
        clamped_position = max(0, min(target_position, len(target_siblings)))
        moved = card.model_copy(update={"column_id": target_column_id})
        target_siblings.insert(clamped_position, moved)

        for index, sibling in enumerate(target_siblings):
            self._cards[sibling.id] = sibling.model_copy(update={"position": index})

        return self._cards[card_id]
