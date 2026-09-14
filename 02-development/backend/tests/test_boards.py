from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_list_boards():
    response = client.post("/boards", json={"name": "Personal"})
    assert response.status_code == 201
    board = response.json()
    assert board["name"] == "Personal"
    assert "id" in board

    response = client.get("/boards")
    assert response.status_code == 200
    assert any(b["id"] == board["id"] for b in response.json())


def test_get_board_returns_columns_and_cards():
    board = client.post("/boards", json={"name": "Work"}).json()
    response = client.get(f"/boards/{board['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["board"]["id"] == board["id"]
    assert body["columns"] == []
    assert body["cards"] == []


def test_get_missing_board_returns_404():
    response = client.get("/boards/does-not-exist")
    assert response.status_code == 404


def test_rename_board():
    board = client.post("/boards", json={"name": "Old name"}).json()
    response = client.patch(f"/boards/{board['id']}", json={"name": "New name"})
    assert response.status_code == 200
    assert response.json()["name"] == "New name"


def test_delete_board():
    board = client.post("/boards", json={"name": "Temp"}).json()
    response = client.delete(f"/boards/{board['id']}")
    assert response.status_code == 204
    assert client.get(f"/boards/{board['id']}").status_code == 404
