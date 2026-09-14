from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_column():
    board = client.post("/boards", json={"name": "Board"}).json()
    return client.post(f"/boards/{board['id']}/columns", json={"name": "To Do"}).json()


def test_create_card():
    column = _make_column()
    response = client.post(
        f"/columns/{column['id']}/cards",
        json={"title": "Write tests", "description": None, "color_label": "blue"},
    )
    assert response.status_code == 201
    card = response.json()
    assert card["title"] == "Write tests"
    assert card["column_id"] == column["id"]
    assert card["position"] == 0


def test_create_card_on_missing_column_returns_404():
    response = client.post("/columns/does-not-exist/cards", json={"title": "X"})
    assert response.status_code == 404


def test_update_card():
    column = _make_column()
    card = client.post(f"/columns/{column['id']}/cards", json={"title": "Draft"}).json()
    response = client.patch(f"/cards/{card['id']}", json={"title": "Final", "color_label": "green"})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Final"
    assert body["color_label"] == "green"


def test_delete_card():
    column = _make_column()
    card = client.post(f"/columns/{column['id']}/cards", json={"title": "Temp"}).json()
    response = client.delete(f"/cards/{card['id']}")
    assert response.status_code == 204


def test_move_card_to_another_column():
    column_a = _make_column()
    board_id = column_a["board_id"]
    column_b = client.post(f"/boards/{board_id}/columns", json={"name": "Done"}).json()
    card = client.post(f"/columns/{column_a['id']}/cards", json={"title": "Ship it"}).json()

    response = client.patch(
        f"/cards/{card['id']}/move",
        json={"target_column_id": column_b["id"], "target_position": 0},
    )
    assert response.status_code == 200
    assert response.json()["column_id"] == column_b["id"]


def test_create_card_requires_title():
    column = _make_column()
    response = client.post(f"/columns/{column['id']}/cards", json={"title": ""})
    assert response.status_code == 422
