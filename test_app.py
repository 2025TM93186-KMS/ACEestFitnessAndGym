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

# region V2.1.2 & V2.2.1
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

# endregion

# region V2.2.1

# ==============================================================================
# NEWLY APPENDED TESTS FOR : v2.2.1
# ==============================================================================

def test_v2_2_1_export_progress_success(client):
    # Seed progress tracking history lines for the query context
    payload = {"name": "Jane", "adherence": 85}
    client.post('/api/v2.1.2/progress', json=payload)

    # Execute endpoint fetch download stream
    response = client.get('/api/v2.2.1/progress/export?name=Jane')
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


def test_v2_2_1_export_progress_missing_name_param(client):
    response = client.get('/api/v2.2.1/progress/export')
    assert response.status_code == 400
    assert "Missing required 'name' filter parameter" in response.json["error"]


def test_v2_2_1_export_progress_client_not_found(client):
    response = client.get('/api/v2.2.1/progress/export?name=UnknownUser')
    assert response.status_code == 404
    assert "No structural timelines logged for UnknownUser" in response.json["error"]

# endregion

# region V2.2.4

# ==============================================================================
# NEWLY APPENDED TESTS FOR : v2.2.4
# ==============================================================================

def test_v2_2_4_health_check(client):
    response = client.get('/api/v2.2.4/health')
    assert response.status_code == 200
    assert response.json['status'] == "healthy"
    assert "V2.2.4 Backend" in response.json['service']


def test_v2_2_4_save_client_success(client):
    payload = {
        "name": "Alex",
        "program": "Fat Loss (FL) – 5 day",
        "age": 25,
        "weight": 90.0,
        "height": 180.0,
        "target_weight": 80.0,
        "target_adherence": 90
    }
    response = client.post('/api/v2.2.4/client', json=payload)
    assert response.status_code == 200
    assert "Client data saved" in response.json["message"]
    # 90.0 weight * 24 factor = 2160 calories expected
    assert response.json["calories"] == 2160
    assert "id" in response.json


def test_v2_2_4_save_client_validation_missing_fields(client):
    payload = {
        "name": "Incomplete Profile"
        # 'program' parameter is missing
    }
    response = client.post('/api/v2.2.4/client', json=payload)
    assert response.status_code == 400
    assert "Name and Program fields are required" in response.json["error"]


def test_v2_2_4_save_client_unrecognized_program(client):
    payload = {
        "name": "Invalid Program User",
        "program": "Hyper-Bulk 6 Day Split",
        "weight": 75.0
    }
    response = client.post('/api/v2.2.4/client', json=payload)
    assert response.status_code == 404
    assert "matches no baseline" in response.json["error"]



def test_v2_2_4_load_client_profile_success(client):
    """Ensures a client's full metrics payload merges and tracks accurately from all tables."""
    # 1. Use an active SQLite connection context to manually seed test rows across tables
    from app import get_db
    with get_db() as conn:
        cur = conn.cursor()

        # Seed core profile
        cur.execute("""
            INSERT INTO clients (name, age, height, weight, program, calories, target_weight, target_adherence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("David", 29, 182.5, 88.0, "Muscle Gain (MG) – PPL", 3080, 85.0, 95))

        # Seed progress metrics lines (2 weeks logging 90% and 100% adherence -> average 95.0%)
        cur.execute("INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)", ("David", "W1", 90))
        cur.execute("INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)", ("David", "W2", 100))

        # Seed body history snapshots (Newest record should override old ones)
        cur.execute("INSERT INTO metrics (client_name, date, weight, waist, bodyfat) VALUES (?, ?, ?, ?, ?)",
                    ("David", "2026-10-01", 89.0, 86.0, 16.5))
        cur.execute("INSERT INTO metrics (client_name, date, weight, waist, bodyfat) VALUES (?, ?, ?, ?, ?)",
                    ("David", "2026-10-07", 88.0, 85.0, 16.0))  # Most Recent

        conn.commit()

    # 2. Query target profile entry via route
    response = client.get('/api/v2.2.4/client?name=David')
    assert response.status_code == 200

    data = response.json

    # Profile Validation
    assert data["CLIENT PROFILE"]["name"] == "David"
    assert data["CLIENT PROFILE"]["calories"] == "3080 kcal/day"
    assert data["CLIENT PROFILE"]["height"] == "182.5 cm"

    # Progress Summary Accumulations Validation
    assert data["PROGRESS SUMMARY"]["Weeks logged"] == 2
    assert data["PROGRESS SUMMARY"]["Average adherence"] == "95.0%"

    # Goals Validation
    assert "Target Weight: 85.0 kg" in data["GOALS"]["summary"]
    assert "Target Adherence: 95%" in data["GOALS"]["summary"]

    # Most Recent Metric Override Filter Validation
    expected_metric_str = "2026-10-07 | 88.0 kg, Waist 85.0 cm, Bodyfat 16.0%"
    assert data["LAST BODY METRICS"]["summary"] == expected_metric_str


def test_v2_2_4_load_client_profile_no_history(client):
    from app import get_db
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO clients (name, age, height, weight, program, calories, target_weight, target_adherence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("NoHistoryUser", 40, None, None, "Beginner (BG)", 2000, 0.0, 0))
        conn.commit()

    response = client.get('/api/v2.2.4/client?name=NoHistoryUser')
    assert response.status_code == 200

    data = response.json
    assert data["CLIENT PROFILE"]["height"] == "-"
    assert data["CLIENT PROFILE"]["weight"] == "-"
    assert data["GOALS"]["summary"] == "None"
    assert data["LAST BODY METRICS"]["summary"] == "None"
    assert data["PROGRESS SUMMARY"]["Weeks logged"] == 0
    assert data["PROGRESS SUMMARY"]["Average adherence"] == "0%"


def test_v2_2_4_load_client_missing_name_param(client):
    response = client.get('/api/v2.2.4/client')
    assert response.status_code == 400
    assert response.json["error"] == "Missing 'name' query parameter"


def test_v2_2_4_load_client_not_found(client):
    response = client.get('/api/v2.2.4/client?name=MissingClient')
    assert response.status_code == 404
    assert response.json["error"] == "Client not found"

# endregion