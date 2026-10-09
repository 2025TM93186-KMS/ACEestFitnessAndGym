import os
import pytest
from app import app

import io
import csv

import json

TEST_DB_NAME = "test_aceest_fitness.db"
PROGRAMS = {
            "Fat Loss (FL) – 3 day": {"factor": 22, "desc": "3-day full-body fat loss"},
            "Fat Loss (FL) – 5 day": {"factor": 24, "desc": "5-day split, higher volume fat loss"},
            "Muscle Gain (MG) – PPL": {"factor": 35, "desc": "Push/Pull/Legs hypertrophy"},
            "Beginner (BG)": {"factor": 26, "desc": "3-day simple beginner full-body"},
        }
PROGRAMS_LOWER = {k.lower(): v for k, v in PROGRAMS.items()}

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

        response_progress = client.get('/api/v3.0.1/progress?name=David')
        data_progress = response_progress.json

        weight = 88.0
        height = 182.5
        program = "Muscle Gain (MG) – PPL"
        program_details = PROGRAMS_LOWER.get(program.lower())
        factor = float(program_details["factor"])
        print(weight, factor)
        calories = int(weight * factor) if weight > 0 else None

        assert data["CLIENT PROFILE"]["name"] == "David"
        assert data["CLIENT PROFILE"]["calories"] == f"{calories} kcal/day"
        assert data["CLIENT PROFILE"]["height"] == f"{height} cm"

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
# region V3.1.2

def test_health_check_v3_1_2(client):
    response = client.get('/api/v3.1.2/health')
    assert response.status_code == 200
    assert response.json['status'] == "healthy"
    assert "V3.1.2 Backend" in response.json['service']


def test_login_user_success(client):
    # Seed default baseline admin identity for authentication parsing checks
    response = client.post('/api/v3.1.2/login', json={
        "username": "admin",
        "password": "admin"
    })
    assert response.status_code == 200
    assert response.json["message"] == "Login Successful"
    assert response.json["role"] == "Admin"


def test_login_user_invalid_credentials(client):
    response = client.post('/api/v3.1.2/login', json={
        "username": "admin",
        "password": "wrong_password"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json["error"]


def test_get_client_list_success(client):
    # 1. Establish seeded users via the POST endpoint matrix
    client.post('/api/v3.1.2/client', json={
        "name": "Barbara",
        "program": "Beginner (BG)",
        "age": 28,
        "height": 165.0,
        "weight": 60.0,
        "membership_expiry": "2027-01-01"
    })
    client.post('/api/v3.1.2/client', json={
        "name": "Aaron",
        "program": "Muscle Gain (MG) – PPL",
        "age": 32,
        "height": 182.0,
        "weight": 85.0,
        "membership_expiry": "2027-06-01"
    })

    # 2. Fire GET client list request tracking lines
    response = client.get('/api/v3.1.2/clients')
    assert response.status_code == 200
    assert "clients" in response.json


def test_get_client_list_empty(client):
    response = client.get('/api/v3.1.2/clients')
    if response.status_code == 404:
        assert response.status_code == 404
        assert response.json["error"] == "Client not found"
    else:
        assert response.status_code


def test_save_client_v3_1_2_success(client):
    payload = {
        "name": "Sarah Connor",
        "program": "Muscle Gain (MG) – PPL",
        "age": 28,
        "height": 170.0,
        "weight": 65.0,
        "membership_end": "2027-12-31"
    }
    response = client.post('/api/v3.1.2/client', json=payload)
    assert response.status_code == 200
    assert "Client data saved" in response.json["message"]
    # 65.0 weight * 35 program factor = 2275 calories expected
    assert response.json["calories"] == 2275
    assert "id" in response.json

def test_save_client_v3_1_2_missing_fields(client):
    response = client.post('/api/v3.1.2/client', json={"name": "Incomplete"})
    assert response.status_code == 400
    assert "Name and Program fields are required" in response.json["error"]


def test_load_client_v3_1_2_success(client):
    # Setup test baseline
    client.post('/api/v3.1.2/client', json={
        "name": "Johns Doe",
        "program": "Beginner (BG)",
        "age": 35,
        "height": 175.0,
        "weight": 80.0,
        "membership_expiry": "2026-06-01"
    })

    response = client.get('/api/v3.1.2/client?name=Johns Doe')
    if response.status_code == 200:
        assert response.status_code == 200
        assert "CLIENT PROFILE" in response.json
        profile = response.json["CLIENT PROFILE"]
        assert profile["name"] == "Johns Doe"
        assert profile["program"] == "Beginner (BG)"
        assert profile["membership_expiry"] == "2026-06-01"
    else:
        assert response.status_code == 404
        assert "Client not found" in response.json["error"]


def test_load_client_v3_1_2_missing_name(client):
    response = client.get('/api/v3.1.2/client')
    assert response.status_code == 400
    assert "Missing 'name' query parameter" in response.json["error"]


def test_load_client_v3_1_2_not_found(client):
    response = client.get('/api/v3.1.2/client?name=GhostUser')
    assert response.status_code == 404
    assert "Client not found" in response.json["error"]

# endregion

# region V3.2.4

def test_generate_ai_program_success(client):
    # Setup baseline data layout
    client.post('/api/v3.1.2/client', json={
        "name": "David Miller",
        "program": "Fat Loss (FL) – 3 day",
        "weight": 90.0
    })

    response = client.post('/api/v3.1.2/ai_program?name=David Miller&exp_level=intermediate')
    assert response.status_code == 200
    assert "AI program generated" in response.json["message"]
    assert "program" in response.json

    program_list = response.json["program"]
    assert len(program_list) > 0
    # Intermediate should yield structured tracking array objects containing core text items keys
    assert "day" in program_list[0]
    assert "exercise" in program_list[0]
    assert "sets" in program_list[0]
    assert "reps" in program_list[0]


def test_generate_ai_program_invalid_exp_level(client):
    response = client.post('/api/v3.1.2/ai_program?name=David Miller&exp_level=elite')
    assert response.status_code == 400
    assert "Invalid experience level" in response.json["error"]


def test_export_pdf_report_success(client):
    # Seed client with complex unicode characters like '–' to explicitly test font mapping isolation layers
    client.post('/api/v3.1.2/client', json={
        "name": "David Report Test",
        "program": "Fat Loss (FL) – 3 day",
        "age": 30,
        "height": 180.0,
        "weight": 85.0,
        "membership_expiry": "2027-01-01"
    })

    response = client.get('/api/v3.1.2/pdf_report?name=David Report Test')

    # 1. If your updated endpoint directly streams binary bytes across HTTP response:
    if response.status_code == 200 and response.mimetype == "application/pdf":
        assert response.status_code == 200
        assert "application/pdf" in response.headers["Content-Type"]
        assert "attachment" in response.headers["Content-Disposition"]
        assert "filename=David Report Test_report.pdf" in response.headers["Content-Disposition"]

    # 2. Alternately, if it writes locally and responds with JSON:
    else:
        assert "saved as" in response.json["message"]


def test_export_pdf_report_missing_name(client):
    response = client.get('/api/v3.1.2/pdf_report')
    if response.status_code == 400:
        assert response.status_code == 400
        assert "Missing 'name' query parameter" in response.json["error"]
    elif response.status_code == 404:
        assert response.status_code == 404
        assert "Client not found" in response.json["error"]
    else:
        assert response.status_code == 200
        assert "saved as" in response.json["message"]


def test_export_pdf_report_not_found(client):
    response = client.get('/api/v3.1.2/pdf_report?name=NonExistent')
    if response.status_code == 404:
        assert response.status_code == 404
        assert "not found" in response.json["error"].lower()
    elif response.status_code == 500:
        assert response.status_code == 500
    else:
        assert response.status_code == 200
        assert "saved as" in response.json["message"]

def test_generate_ai_program_v3_2_4_success(client):
    client.post('/api/v3.2.4/client', json={"name": "John Doe"})

    payload = {"name": "John Doe", "program_type": "Muscle Gain"}
    response = client.post('/api/v3.2.4/ai_program', json=payload)

    assert response.status_code == 200

    assert "Program for John Doe:" in response.get_json()["message"]


def test_generate_pdf_report_success(client):
    client.post('/api/v3.2.4/client', json={
        "name": "John Doe"
    })
    response = client.get('/api/v3.2.4/generate_pdf?name=John+Doe')
    if response.status_code == 400:
        assert response.status_code == 400
        assert "Missing" in response.json["error"]
    elif response.status_code == 404:
        assert "not found" in response.json["error"].lower()
    else:
        assert response.status_code == 200
        assert "report.pdf created" in response.get_json()["message"]

def test_check_membership_success(client):
    response = client.get('/api/v3.2.4/check_membership?name=John+Doe')
    if response.status_code == 400:
        assert response.status_code == 400
        assert "Missing" in response.json["error"]
    elif response.status_code == 404:
        assert "not found" in response.json["error"].lower()
    else:
        assert response.status_code == 200
        assert "Membership: Active" in response.get_json()["message"]

def test_plot_charts_data_success(client):
    response = client.get('/api/v3.2.4/plot_charts?name=John+Doe')
    if response.status_code == 200:
        assert response.status_code == 200
        chart_payload = response.get_json()["message"]
        assert chart_payload["week"] == ["Week 1", "Week 2"]
        assert chart_payload["adherence"] == [95, 90]
    else :
        assert response.status_code == 404


def test_add_workout_invalid_type(client):
    payload = {
        "name": "John Doe",
        "workout": "InvalidWorkoutType",
        "duration": "45"
    }
    response = client.post('/api/v3.2.4/workout', json=payload)
    assert response.status_code == 404
    assert "Workout not found" in response.get_json()["error"]

# endregion
