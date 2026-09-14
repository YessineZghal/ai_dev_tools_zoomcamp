"""SQLAlchemy-backed implementation of the same interface as app.store.Store.

Route handlers in app.main never call this directly by name — they call
whatever `store` is bound to. Swapping Store for SqlStore is the entire
migration from the mock backend to a real database.
"""

from sqlalchemy.orm import Session, sessionmaker

from app.models import BoardModel, CardModel, ColumnModel
from app.schemas import Board, Card, Column


def _board_to_schema(row: BoardModel) -> Board:
    return Board(
        id=row.id,
        name=row.name,
        created_at=row.created_at.isoformat() if row.created_at else "",
    )


def _column_to_schema(row: ColumnModel) -> Column:
    return Column(id=row.id, board_id=row.board_id, name=row.name, position=row.position)


def _card_to_schema(row: CardModel) -> Card:
    return Card(
        id=row.id,
        column_id=row.column_id,
        title=row.title,
        description=row.description,
        color_label=row.color_label,
        position=row.position,
    )


class SqlStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # --- Boards ---

    def list_boards(self) -> list[Board]:
        with self._session_factory() as session:
            rows = session.query(BoardModel).all()
            return [_board_to_schema(row) for row in rows]

    def create_board(self, name: str) -> Board:
        with self._session_factory() as session:
            row = BoardModel(name=name)
            session.add(row)
            session.commit()
            session.refresh(row)
            return _board_to_schema(row)

    def get_board(self, board_id: str) -> Board | None:
        with self._session_factory() as session:
            row = session.get(BoardModel, board_id)
            return _board_to_schema(row) if row else None

    def rename_board(self, board_id: str, name: str) -> Board | None:
        with self._session_factory() as session:
            row = session.get(BoardModel, board_id)
            if row is None:
                return None
            row.name = name
            session.commit()
            session.refresh(row)
            return _board_to_schema(row)

    def delete_board(self, board_id: str) -> bool:
        with self._session_factory() as session:
            row = session.get(BoardModel, board_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    # --- Columns ---

    def list_columns(self, board_id: str) -> list[Column]:
        with self._session_factory() as session:
            rows = (
                session.query(ColumnModel)
                .filter(ColumnModel.board_id == board_id)
                .order_by(ColumnModel.position)
                .all()
            )
            return [_column_to_schema(row) for row in rows]

    def list_cards_for_board(self, board_id: str) -> list[Card]:
        with self._session_factory() as session:
            rows = (
                session.query(CardModel)
                .join(ColumnModel, CardModel.column_id == ColumnModel.id)
                .filter(ColumnModel.board_id == board_id)
                .all()
            )
            return [_card_to_schema(row) for row in rows]

    def get_column(self, column_id: str) -> Column | None:
        with self._session_factory() as session:
            row = session.get(ColumnModel, column_id)
            return _column_to_schema(row) if row else None

    def create_column(self, board_id: str, name: str) -> Column:
        with self._session_factory() as session:
            position = (
                session.query(ColumnModel).filter(ColumnModel.board_id == board_id).count()
            )
            row = ColumnModel(board_id=board_id, name=name, position=position)
            session.add(row)
            session.commit()
            session.refresh(row)
            return _column_to_schema(row)

    def rename_column(self, column_id: str, name: str) -> Column | None:
        with self._session_factory() as session:
            row = session.get(ColumnModel, column_id)
            if row is None:
                return None
            row.name = name
            session.commit()
            session.refresh(row)
            return _column_to_schema(row)

    def delete_column(self, column_id: str) -> bool:
        with self._session_factory() as session:
            row = session.get(ColumnModel, column_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    def reorder_columns(self, board_id: str, ordered_ids: list[str]) -> list[Column]:
        with self._session_factory() as session:
            for index, column_id in enumerate(ordered_ids):
                row = session.get(ColumnModel, column_id)
                if row is not None:
                    row.position = index
            session.commit()
            rows = (
                session.query(ColumnModel)
                .filter(ColumnModel.board_id == board_id)
                .order_by(ColumnModel.position)
                .all()
            )
            return [_column_to_schema(row) for row in rows]

    # --- Cards ---

    def create_card(
        self,
        column_id: str,
        title: str,
        description: str | None,
        color_label: str | None,
    ) -> Card:
        with self._session_factory() as session:
            position = (
                session.query(CardModel).filter(CardModel.column_id == column_id).count()
            )
            row = CardModel(
                column_id=column_id,
                title=title,
                description=description,
                color_label=color_label,
                position=position,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return _card_to_schema(row)

    def update_card(self, card_id: str, **fields) -> Card | None:
        with self._session_factory() as session:
            row = session.get(CardModel, card_id)
            if row is None:
                return None
            for key, value in fields.items():
                setattr(row, key, value)
            session.commit()
            session.refresh(row)
            return _card_to_schema(row)

    def delete_card(self, card_id: str) -> bool:
        with self._session_factory() as session:
            row = session.get(CardModel, card_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True

    def move_card(self, card_id: str, target_column_id: str, target_position: int) -> Card | None:
        with self._session_factory() as session:
            moving = session.get(CardModel, card_id)
            if moving is None:
                return None

            siblings = (
                session.query(CardModel)
                .filter(CardModel.column_id == target_column_id, CardModel.id != card_id)
                .order_by(CardModel.position)
                .all()
            )
            clamped_position = max(0, min(target_position, len(siblings)))
            siblings.insert(clamped_position, moving)

            moving.column_id = target_column_id
            for index, sibling in enumerate(siblings):
                sibling.position = index

            session.commit()
            session.refresh(moving)
            return _card_to_schema(moving)
