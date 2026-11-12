from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from conftest import app


client = TestClient(app)


def _mock_connection(monkeypatch):
    connection = MagicMock()
    connection.__enter__.return_value = connection
    monkeypatch.setattr("main.get_db", lambda: connection)
    return connection


def test_existing_task_list_and_detail_routes(monkeypatch):
    connection = _mock_connection(monkeypatch)
    connection.execute.return_value.fetchall.return_value = [
        {"id": 1, "title": "Learn FastAPI", "done": False}
    ]

    list_response = client.get("/tasks")

    assert list_response.status_code == 200
    assert list_response.json() == [
        {"id": 1, "title": "Learn FastAPI", "done": False}
    ]

    connection.execute.return_value.fetchone.return_value = {
        "id": 1,
        "title": "Learn FastAPI",
        "done": False,
    }
    detail_response = client.get("/tasks/1")

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == 1


def test_existing_task_create_update_and_delete_routes(monkeypatch):
    connection = _mock_connection(monkeypatch)
    connection.execute.return_value.fetchone.return_value = {
        "id": 2,
        "title": "Review auth",
        "done": False,
    }

    create_response = client.post(
        "/tasks",
        json={"title": "Review auth", "done": False},
    )
    assert create_response.status_code == 201
    assert create_response.json()["id"] == 2

    update_response = client.put(
        "/tasks/2",
        json={"title": "Review auth", "done": True},
    )
    assert update_response.status_code == 200
    assert update_response.json()["id"] == 2

    connection.execute.return_value.rowcount = 1
    delete_response = client.delete("/tasks/2")
    assert delete_response.status_code == 204
    assert delete_response.content == b""
