import os
import pytest
from app import app, CLIENTS_DB

TEST_DB_NAME = "test_aceest_fitness.db"

@pytest.fixture
def client(monkeypatch):
    """Initializes a sandboxed test environment and patch tracking variable parameters."""
    app.config['TESTING'] = True
    CLIENTS_DB.clear()

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



# ==============================================================================
# MULTI-VERSION HEALTH ENDPOINT TESTS (v1.0, v1.1, v2.0.1)
# ==============================================================================

def test_health_check_v1_0(client):
    """Verify v1.0 health check route responds successfully."""
    response = client.get('/api/v1.0/health')
    assert response.status_code == 200
    assert "V1.0 Backend" in response.json['service']


def test_health_check_v1_1(client):
    """Verify v1.1 health check route responds successfully."""
    response = client.get('/api/v1.1/health')
    assert response.status_code == 200
    assert "V1.1 Backend" in response.json['service']


def test_health_check_v2_0_1(client):
    """Verify v2.0.1 health check route responds successfully."""
    response = client.get('/api/v2.0.1/health')
    assert response.status_code == 200
    assert "V2.0.1 Backend" in response.json['service']


# ==============================================================================
# V1.0 ENDPOINT TEST CASES
# ==============================================================================

def test_v1_0_get_programs(client):
    """Verify retrieval mapping works for available workout tracks."""
    response = client.get('/api/v1.0/programs')
    assert response.status_code == 200
    assert "Fat Loss (FL)" in response.json['programs']


def test_v1_0_entire_plan_success(client):
    response = client.get('/api/v1.0/entire_plan?program_name=Muscle Gain (MG)')
    assert response.status_code == 200
    assert "Chicken Biryani" in response.json['daily_nutrition_plan']
    assert response.json['ui_color'] == "#2ecc71"


def test_v1_0_entire_plan_missing_param(client):
    response = client.get('/api/v1.0/entire_plan')
    assert response.status_code == 400
    assert "Missing required 'program_name'" in response.json['error']


def test_v1_0_entire_plan_not_found(client):
    response = client.get('/api/v1.0/entire_plan?program_name=Nonexistent')
    assert response.status_code == 404
    assert "not found" in response.json['error']


def test_v1_0_weekly_workout_chart(client):
    response = client.get('/api/v1.0/weekly_workout_chart?program_name=fat loss (fl)')
    assert response.status_code == 200
    assert "Back Squat" in response.json['weekly_workout_chart']


def test_v1_0_daily_nutrition_plan(client):
    response = client.get('/api/v1.0/daily_nutrition_plan?program_name=Beginner (BG)')
    assert response.status_code == 200
    assert "Balanced Tamil Meals" in response.json['daily_nutrition_plan']


# ==============================================================================
# V1.1 CALORIE ESTIMATION TEST CASES
# ==============================================================================

def test_v1_1_calculate_calories_success(client):
    """Verifies that calorie factor formulas execute accurately under POST requests."""
    payload = {"program": "Fat Loss (FL)", "weight": 80.0}
    response = client.post('/api/v1.1/calculate_calories', json=payload)
    assert response.status_code == 200
    assert response.json["calories"] == "1760 kcal"  # 80 * 22 = 1760


def test_v1_1_calculate_calories_fallback(client):
    """Ensures empty structural metrics safely drop to default strings."""
    response = client.post('/api/v1.1/calculate_calories', json={})
    assert response.status_code == 200
    assert response.json["calories"] == "--"


# ==============================================================================
# V1.1.2 IN-MEMORY ENGINE TEST CASES
# ==============================================================================

def test_v1_1_2_save_client_success(client):
    """Ensure validation records parse, transform fields, and append to the list cache."""
    payload = {
        "name": "Marcus",
        "program": "Muscle Gain (MG)",
        "age": 30,
        "weight": 85.5,
        "progress": 95,
        "notes": "Excellent lifting structure base"
    }
    response = client.post('/api/v1.1.2/save_client', json=payload)
    assert response.status_code == 200
    assert "validated and processed successfully" in response.json["success"]
    assert response.json["client_summary"]["name"] == "Marcus"
    assert len(CLIENTS_DB) == 1


def test_v1_1_2_save_client_validation_missing_fields(client):
    """Checks for 400 status parameters if required registration keys are empty."""
    payload = {"name": "", "program": "Fat Loss (FL)"}
    response = client.post('/api/v1.1.2/save_client', json=payload)
    assert response.status_code == 400
    assert "Please fill client name and program" in response.json["error"]


def test_v1_1_2_save_client_invalid_program(client):
    """Checks for 400 status parameters if the requested track is not found."""
    payload = {"name": "Alex", "program": "Invalid Track"}
    response = client.post('/api/v1.1.2/save_client', json=payload)
    assert response.status_code == 400
    assert "not found" in response.json["error"]


def test_v1_1_2_save_client_invalid_metrics(client):
    """Ensures improper numeric formatting triggers a 400 gate block."""
    payload = {
        "name": "Alex",
        "program": "Beginner (BG)",
        "age": "thirty",  # Invalid integer format
        "weight": 70.0
    }
    response = client.post('/api/v1.1.2/save_client', json=payload)
    assert response.status_code == 400
    assert "Invalid format for numeric metrics" in response.json["error"]


def test_v1_1_2_get_clients_list(client):
    """Verifies retrieval arrays track context entries sequentially."""
    # Seed a target record structure
    CLIENTS_DB.append({
        "name": "Jane", "age": 28, "weight": 60.0,
        "program": "Fat Loss (FL)", "adherence": 85, "notes": "No notes"
    })

    response = client.get('/api/v1.1.2/clients')
    assert response.status_code == 200
    assert len(response.json["clients"]) == 1
    assert response.json["clients"][0]["name"] == "Jane"


def test_v1_1_2_export_csv_success(client):
    """Verifies that client tracking lists convert cleanly and stream down functional CSV files."""
    # Seed mock information
    CLIENTS_DB.append({
        "name": "Sarah Lee", "age": 29, "weight": 65.0,
        "program": "Beginner (BG)", "adherence": 90, "notes": "Focusing on form"
    })

    response = client.get('/api/v1.1.2/export_csv')
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "attachment; filename=aceest_clients.csv" in response.headers["Content-Disposition"]

    csv_text = response.data.decode("utf-8")
    assert "Name,Age,Weight,Program" in csv_text
    assert "Sarah Lee,29,65.0" in csv_text


def test_v1_1_2_export_csv_empty_error_boundary(client):
    """Validates boundary error triggers if client attempts to parse empty metrics."""
    response = client.get('/api/v1.1.2/export_csv')
    assert response.status_code == 400
    assert "No clients to export" in response.json["error"]


def test_v1_1_2_clear_clients(client):
    """Confirms that calling clear destroys the transient in-memory store states."""
    CLIENTS_DB.append({
        "name": "Jane", "age": 28, "weight": 60.0,
        "program": "Fat Loss (FL)", "adherence": 85, "notes": ""
    })
    assert len(CLIENTS_DB) == 1

    response = client.delete('/api/v1.1.2/clear_clients')
    assert response.status_code == 200
    assert "cleared successfully" in response.json["success"]
    assert len(CLIENTS_DB) == 0


# ==============================================================================
# V2.0.1 CORE DATABASE INTEGRATION TESTS (AUTO-INITIALIZATION LIFE CYCLE)
# ==============================================================================

def test_v2_0_1_save_client_success(client):
    """Ensure validation records parse and commit to disk storage handles."""
    payload = {
        "name": "Marcus",
        "program": "Muscle Gain (MG)",
        "age": 30,
        "weight": 85.5
    }
    response = client.post('/api/v2.0.1/client', json=payload)
    assert response.status_code == 200
    assert "Client data saved" in response.json["message"]
    assert response.json["calories"] == int(85.5 * 35)


def test_v2_0_1_save_client_validation_missing_fields(client):
    """Checks for 400 status parameters if required registration keys are missing."""
    payload = {"name": "", "program": "Fat Loss (FL)"}
    response = client.post('/api/v2.0.1/client', json=payload)
    assert response.status_code == 400
    assert "fields are required" in response.json["error"]


def test_v2_0_1_load_client_success(client):
    """Verifies data can be securely read."""
    # Seed data
    payload = {"name": "Jane", "program": "Fat Loss (FL)", "age": 28, "weight": 60.0}
    client.post('/api/v2.0.1/client', json=payload)

    # Attempt query fetch
    response = client.get('/api/v2.0.1/client?name=Jane')
    assert response.status_code == 200
    assert response.json["name"] == "Jane"
    assert response.json["program"] == "Fat Loss (FL)"
    assert response.json["calories"] == int(60.0 * 22)


def test_v2_0_1_load_client_not_found(client):
    """Verifies targeted missing entries with 404."""
    response = client.get('/api/v2.0.1/client?name=GhostUser')
    assert response.status_code == 404
    assert "not found" in response.json["error"]


def test_v2_0_1_save_progress_success(client):
    payload = {
        "name": "Marcus",
        "adherence": 90
    }
    response = client.post('/api/v2.0.1/progress', json=payload)
    assert response.status_code == 201
    assert "Weekly progress logged" in response.json["message"]
