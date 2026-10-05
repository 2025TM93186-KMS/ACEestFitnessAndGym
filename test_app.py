import pytest
from app import app

@pytest.fixture
def client():
    """Initializes a sandboxed test client instance for testing routes"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_api_v1_0_root(client):
    response = client.get('/api/v1.0')
    assert response.status_code == 200
    assert response.json['version'] == "1.0"
    assert response.json['metrics_summary']['capacity_users'] == 150

def test_health_check(client):
    response = client.get('/api/v1.0/health')
    assert response.status_code == 200
    assert response.json['status'] == "healthy"

def test_get_programs_list(client):
    """Validates that the program tracking arrays map accurately"""
    response = client.get('/api/v1.0/programs')
    assert response.status_code == 200
    assert "Fat Loss (FL)" in response.json['programs']

def test_entire_plan_successful_lookup(client):
    """Confirms complete plans parse and match structural string contents"""
    response = client.get('/api/v1.0/entire_plan?program_name=Muscle Gain (MG)')
    assert response.status_code == 200
    assert response.json['ui_color'] == "#2ecc71"
    assert "Chicken Biryani" in response.json['daily_nutrition_plan']

def test_case_insensitive_workout_lookup(client):
    response = client.get('/api/v1.0/weekly_workout_chart?program_name=fat loss (fl)')
    assert response.status_code == 200
    assert "Back Squat" in response.json['weekly_workout_chart']

def test_case_insensitive_nutrition_lookup(client):
    response = client.get('/api/v1.0/daily_nutrition_plan?program_name=mUsCLe GaIn (Mg)')
    assert response.status_code == 200
    assert "~3200 kcal" in response.json['daily_nutrition_plan']

def test_missing_parameter_error_gate(client):
    """Validates robust exception mapping when client leaves arguments blank"""
    response = client.get('/api/v1.0/entire_plan')
    assert response.status_code == 400
    assert "Missing required 'program_name'" in response.json['error']

def test_invalid_plan_not_found_boundary(client):
    response = client.get('/api/v1.0/entire_plan?program_name=Zumba')
    assert response.status_code == 404
    assert "not found" in response.json['error']

def test_weekly_workout_chart_missing_parameter(client):
    response = client.get('/api/v1.0/weekly_workout_chart')
    assert response.status_code == 400
    assert "Missing 'program_name'" in response.json['error']

def test_daily_nutrition_plan_missing_parameter(client):
    response = client.get('/api/v1.0/daily_nutrition_plan')
    assert response.status_code == 400
    assert "Missing 'program_name'" in response.json['error']


# ==========================================
# NEW V1.1 ENDPOINT TESTS
# ==========================================

def test_calculate_calories_success(client):
    payload = {"program": "Muscle Gain (MG)", "weight": 80}
    response = client.post('/api/v1.1/calculate_calories', json=payload)
    assert response.status_code == 200
    assert response.json["calories"] == "2800 kcal"  # 80 * 35 = 2800


def test_calculate_calories_case_insensitive(client):
    payload = {"program": "fat loss (fl)", "weight": 100}
    response = client.post('/api/v1.1/calculate_calories', json=payload)
    assert response.status_code == 200
    assert response.json["calories"] == "2200 kcal"  # 100 * 22 = 2200


def test_calculate_calories_invalid_inputs(client):
    # Empty payload
    resp_empty = client.post('/api/v1.1/calculate_calories', json={})
    assert resp_empty.json["calories"] == "--"

    # Negative weight
    resp_neg = client.post('/api/v1.1/calculate_calories', json={"program": "Beginner (BG)", "weight": -50})
    assert resp_neg.json["calories"] == "--"


def test_save_client_success(client):
    payload = {
        "name": "Jane",
        "program": "Muscle Gain (MG)",
        "age": 25,
        "weight": 70,
        "progress": 90
    }
    response = client.post('/api/v1.1/save_client', json=payload)
    assert response.status_code == 200
    assert "validated and processed successfully" in response.json["success"]
    assert response.json["adherence"] == 90
    assert response.json["calculated_calories"] == 2450  # 70 * 35 = 2450


def test_save_client_validation_missing_fields(client):
    payload = {"name": "", "program": "Fat Loss (FL)"}
    response = client.post('/api/v1.1/save_client', json=payload)
    assert response.status_code == 400
    assert "Please fill client name and program" in response.json["error"]


def test_save_client_invalid_program(client):
    payload = {"name": "Alex", "program": "Non Existent Workout"}
    response = client.post('/api/v1.1/save_client', json=payload)
    assert response.status_code == 400
    assert "not found" in response.json["error"]


def test_save_client_malformed_numeric_types(client):
    payload = {
        "name": "Bob",
        "program": "Beginner (BG)",
        "age": "invalid_string",
        "weight": "invalid_string",
        "progress": "invalid_string"
    }
    response = client.post('/api/v1.1/save_client', json=payload)
    assert response.status_code == 400
    assert "Invalid format for numeric metrics" in response.json["error"]
