from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_board():
    return client.post("/boards", json={"name": "Board"}).json()


def test_create_column():
    board = _make_board()
    response = client.post(f"/boards/{board['id']}/columns", json={"name": "To Do"})
    assert response.status_code == 201
    column = response.json()
    assert column["name"] == "To Do"
    assert column["board_id"] == board["id"]
    assert column["position"] == 0


def test_second_column_gets_next_position():
    board = _make_board()
    client.post(f"/boards/{board['id']}/columns", json={"name": "To Do"})
    response = client.post(f"/boards/{board['id']}/columns", json={"name": "Done"})
    assert response.json()["position"] == 1


def test_create_column_on_missing_board_returns_404():
    response = client.post("/boards/does-not-exist/columns", json={"name": "To Do"})
    assert response.status_code == 404


def test_rename_and_delete_column():
    board = _make_board()
    column = client.post(f"/boards/{board['id']}/columns", json={"name": "To Do"}).json()

    renamed = client.patch(f"/columns/{column['id']}", json={"name": "Doing"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Doing"

    deleted = client.delete(f"/columns/{column['id']}")
    assert deleted.status_code == 204


def test_reorder_columns():
    board = _make_board()
    first = client.post(f"/boards/{board['id']}/columns", json={"name": "A"}).json()
    second = client.post(f"/boards/{board['id']}/columns", json={"name": "B"}).json()

    response = client.patch(
        f"/columns/{first['id']}/reorder",
        json={"ordered_ids": [second["id"], first["id"]]},
    )
    assert response.status_code == 200
    by_id = {c["id"]: c["position"] for c in response.json()}
    assert by_id[second["id"]] == 0
    assert by_id[first["id"]] == 1
