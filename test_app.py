import os
import pytest
from app import app

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

def test_health_check(client):
    response = client.get('/api/v2.1.2/health')
    assert response.status_code == 200
    assert "V2.1.2 Backend" in response.json['service']


# ==============================================================================
# V2.1.2 CORE DATABASE INTEGRATION TESTS (AUTO-INITIALIZATION LIFE CYCLE)
# ==============================================================================

def test_v2_1_2_save_client_success(client):
    """Ensure validation records parse and commit to disk storage handles."""
    payload = {
        "name": "Marcus",
        "program": "Muscle Gain (MG)",
        "age": 30,
        "weight": 85.5
    }
    response = client.post('/api/v2.1.2/client', json=payload)
    assert response.status_code == 200
    assert "Client data saved" in response.json["message"]
    assert response.json["calories"] == int(85.5 * 35)


def test_v2_1_2_save_client_validation_missing_fields(client):
    """Checks for 400 status parameters if required registration keys are missing."""
    payload = {"name": "", "program": "Fat Loss (FL)"}
    response = client.post('/api/v2.1.2/client', json=payload)
    assert response.status_code == 400
    assert "fields are required" in response.json["error"]


def test_v2_1_2_load_client_success(client):
    # Seed data
    payload = {"name": "Jane", "program": "Fat Loss (FL)", "age": 28, "weight": 60.0}
    client.post('/api/v2.1.2/client', json=payload)

    # Attempt query fetch
    response = client.get('/api/v2.1.2/client?name=Jane')
    assert response.status_code == 200
    assert response.json["name"] == "Jane"
    assert response.json["program"] == "Fat Loss (FL)"
    assert response.json["calories"] == int(60.0 * 22)


def test_v2_1_2_load_client_not_found(client):
    """Verifies targeted missing entries with 404."""
    response = client.get('/api/v2.1.2/client?name=GhostUser')
    assert response.status_code == 404
    assert "not found" in response.json["error"]


def test_v2_1_2_save_progress_success(client):
    payload = {
        "name": "Marcus",
        "adherence": 90
    }
    response = client.post('/api/v2.1.2/progress', json=payload)
    assert response.status_code == 201
    assert "Weekly progress logged" in response.json["message"]
