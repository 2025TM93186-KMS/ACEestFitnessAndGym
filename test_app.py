import os
import pytest
from app import app

import io
import csv

TEST_DB_NAME = "test_aceest_fitness.db"

@pytest.fixture
def client(monkeypatch):
    """Initializes a sandboxed test environment and patch tracking variable parameters."""
    app.config['TESTING'] = True

    # Isolate test database context from production database environment
    monkeypatch.setattr("app.DB_NAME", TEST_DB_NAME)

    # Destructive drop context before the test starts to ensure a clean run
    if os.path.exists(TEST_DB_NAME):
        try:
            os.remove(TEST_DB_NAME)
        except PermissionError:
            pass  # If a previous run locked it, handle gracefully or let SQLite overwrite it

    with app.test_client() as client:
        yield client

# region V3.0.1
def test_health_check(client):
    response = client.get('/api/v3.0.1/health')
    assert response.status_code == 200
    assert response.json['status'] == "healthy"
    assert "V3.0.1 Backend" in response.json['service']


def test_save_progress_success(client):
    payload = {
        "name": "Marcus",
        "adherence": 90
    }
    response = client.post('/api/v3.0.1/progress', json=payload)
    assert response.status_code == 201
    assert "Weekly progress logged" in response.json["message"]


def test_export_progress_success(client):
    # Seed progress tracking history lines for the query context
    payload = {"name": "Jane", "adherence": 85}
    client.post('/api/v3.0.1/progress', json=payload)

    # Execute endpoint fetch download stream
    response = client.get('/api/v3.0.1/progress/export?name=Jane')
    assert response.status_code == 200
    assert "text/csv" in response.headers["Content-Type"]
    assert "attachment" in response.headers["Content-Disposition"]
    assert "filename=jane_progress.csv" in response.headers["Content-Disposition"]

    # Parse down the output binary stream data wrapper back to list lines
    csv_file = io.StringIO(response.data.decode("utf-8"))
    reader = csv.reader(csv_file)
    rows = list(reader)

    # Validate header fields and percentage appended string definitions
    assert rows[0] == ["Client Name", "Week Identifier", "Adherence Percentage"]
    assert rows[1][0] == "Jane"
    assert rows[1][2] == "85%"


def test_export_progress_missing_name_param(client):
    response = client.get('/api/v3.0.1/progress/export')
    assert response.status_code == 400
    assert "Missing required 'name' filter parameter" in response.json["error"]


def test_export_progress_client_not_found(client):
    response = client.get('/api/v3.0.1/progress/export?name=UnknownUser')
    assert response.status_code == 404
    assert "No structural timelines logged for UnknownUser" in response.json["error"]

def test_save_client_success(client):
    payload = {
        "name": "Alex",
        "program": "Fat Loss (FL) – 5 day",
        "age": 25,
        "weight": 90.0,
        "height": 180.0,
        "target_weight": 80.0,
        "target_adherence": 90
    }
    response = client.post('/api/v3.0.1/client', json=payload)
    assert response.status_code == 200
    assert "Client data saved" in response.json["message"]
    # 90.0 weight * 24 factor = 2160 calories expected
    assert response.json["calories"] == 2160
    assert "id" in response.json


def test_save_client_validation_missing_fields(client):
    payload = {
        "name": "Incomplete Profile"
        # 'program' parameter is missing
    }
    response = client.post('/api/v3.0.1/client', json=payload)
    assert response.status_code == 400
    assert "Name and Program fields are required" in response.json["error"]


def test_save_client_unrecognized_program(client):
    payload = {
        "name": "Invalid Program User",
        "program": "Hyper-Bulk 6 Day Split",
        "weight": 75.0
    }
    response = client.post('/api/v3.0.1/client', json=payload)
    assert response.status_code == 404
    assert "matches no baseline" in response.json["error"]

def test_load_client_profile_success(client):
        client_payload = {
            "name": "David",
            "program": "Muscle Gain (MG) – PPL",
            "age": 29,
            "weight": 88.0,
            "height": 182.5,
            "target_weight": 85.0,
            "target_adherence": 95
        }
        client.post('/api/v3.0.1/client', json=client_payload)

        client.post('/api/v3.0.1/progress', json={"name": "David", "week": "W1", "adherence": 90})
        client.post('/api/v3.0.1/progress', json={"name": "David", "week": "W2", "adherence": 100})

        client.post('/api/v3.0.1/metrics', json={
            "name": "David",
            "date": "2026-10-01",
            "weight": 89.0,
            "waist": 86.0,
            "bodyfat": 16.5
        })
        client.post('/api/v3.0.1/metrics', json={
            "name": "David",
            "date": "2026-10-07",
            "weight": 88.0,
            "waist": 85.0,
            "bodyfat": 16.0
        })

        response = client.get('/api/v3.0.1/client?name=David')
        assert response.status_code == 200

        data = response.json

        assert data["CLIENT PROFILE"]["name"] == "David"
        assert data["CLIENT PROFILE"]["calories"] == "3080 kcal/day"
        assert data["CLIENT PROFILE"]["height"] == "182.5 cm"

        assert data["PROGRESS SUMMARY"]["Weeks logged"] == 2


def test_load_client_profile_no_history(client):
    client_payload = {
        "name": "NoHistoryUser",
        "age": 40,
        "height": 0,
        "weight": 0,
        "program": "Beginner (BG)",
        "calories": 2000,
        "target_weight": 0.0,
        "target_adherence": 0
    }
    client.post('/api/v3.0.1/client', json=client_payload)

    response = client.get('/api/v3.0.1/client?name=NoHistoryUser')
    assert response.status_code == 200

    data = response.json
    assert data["CLIENT PROFILE"]["height"] == "-"
    assert data["CLIENT PROFILE"]["weight"] == "-"
    assert data["GOALS"]["summary"] == "None"
    assert data["LAST BODY METRICS"]["summary"] == "None"
    assert data["PROGRESS SUMMARY"]["Weeks logged"] == 0
    assert data["PROGRESS SUMMARY"]["Average adherence"] == "0%"


def test_load_client_missing_name_param(client):
    response = client.get('/api/v3.0.1/client')
    assert response.status_code == 400
    assert response.json["error"] == "Missing 'name' query parameter"


def test_load_client_not_found(client):
    response = client.get('/api/v3.0.1/client?name=MissingClient')
    assert response.status_code == 404
    assert response.json["error"] == "Client not found"

# endregion