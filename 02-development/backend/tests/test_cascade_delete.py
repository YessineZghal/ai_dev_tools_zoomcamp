from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_deleting_board_cascades_to_columns_and_cards():
    board = client.post("/boards", json={"name": "Temp"}).json()
    column = client.post(f"/boards/{board['id']}/columns", json={"name": "To Do"}).json()
    client.post(f"/columns/{column['id']}/cards", json={"title": "Card"})

    response = client.delete(f"/boards/{board['id']}")
    assert response.status_code == 204

    # The column row must be gone too (cascaded), not just orphaned.
    assert client.patch(f"/columns/{column['id']}", json={"name": "x"}).status_code == 404


def test_deleting_column_cascades_to_cards():
    board = client.post("/boards", json={"name": "Board"}).json()
    column = client.post(f"/boards/{board['id']}/columns", json={"name": "To Do"}).json()
    card = client.post(f"/columns/{column['id']}/cards", json={"title": "Card"}).json()

    response = client.delete(f"/columns/{column['id']}")
    assert response.status_code == 204

    # The card row must be gone too (cascaded), not just orphaned.
    assert client.patch(f"/cards/{card['id']}", json={"title": "x"}).status_code == 404
