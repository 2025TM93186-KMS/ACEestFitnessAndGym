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
    assert "3,200 kcal" in response.json['daily_nutrition_plan']

def test_missing_parameter_error_gate(client):
    """Validates robust exception mapping when client leaves arguments blank"""
    response = client.get('/api/v1.0/entire_plan')
    assert response.status_code == 400
    assert "Missing required 'program_name'" in response.json['error']

def test_invalid_plan_not_found_boundary(client):
    response = client.get('/api/v1.0/entire_plan?program_name=Zumba')
    assert response.status_code == 404
