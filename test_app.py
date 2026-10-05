import pytest
from app import app, CLIENTS_DB


@pytest.fixture
def client():
    """Initializes a sandboxed test client instance for testing routes"""
    app.config['TESTING'] = True

    # Clear out volatile state arrays before each discrete test execution loop
    CLIENTS_DB.clear()

    with app.test_client() as client:
        yield client


# ==============================================================================
# MULTI-VERSION HEALTH ENDPOINT TESTS (v1.0, v1.1, v1.1.2)
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


def test_health_check_v1_1_2(client):
    """Verify v1.1.2 health check route responds successfully."""
    response = client.get('/api/v1.1.2/health')
    assert response.status_code == 200
    assert "V1.1.2 Backend" in response.json['service']


# ==============================================================================
# V1.0 ENDPOINT TEST CASES
# ==============================================================================

def test_v1_0_get_programs(client):
    """Verify retrieval mapping works for available workout tracks."""
    response = client.get('/api/v1.0/programs')
    assert response.status_code == 200
    assert "Fat Loss (FL)" in response.json['programs']


def test_v1_0_entire_plan_success(client):
    """Confirms entire plan lookup returns proper status and metadata profiles."""
    response = client.get('/api/v1.0/entire_plan?program_name=Muscle Gain (MG)')
    assert response.status_code == 200
    assert "Eggs, Biryani" in response.json['daily_nutrition_plan']
    assert response.json['ui_color'] == "#2ecc71"


def test_v1_0_entire_plan_missing_param(client):
    """Ensure omitted required parameters trigger a 400 gate block."""
    response = client.get('/api/v1.0/entire_plan')
    assert response.status_code == 400
    assert "Missing required 'program_name'" in response.json['error']


def test_v1_0_entire_plan_not_found(client):
    """Ensure invalid track specifications drop to a 404 block boundary."""
    response = client.get('/api/v1.0/entire_plan?program_name=Nonexistent')
    assert response.status_code == 404
    assert "not found" in response.json['error']


def test_v1_0_weekly_workout_chart(client):
    """Verify weekly workout track retrieval behaves case-insensitively."""
    response = client.get('/api/v1.0/weekly_workout_chart?program_name=fat loss (fl)')
    assert response.status_code == 200
    assert "Back Squat" in response.json['weekly_workout_chart']


def test_v1_0_daily_nutrition_plan(client):
    """Verify daily diet parameters map accurately."""
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
# V1.1.2 VERSION TRACKING & ENGINE OPERATION TESTS
# ==============================================================================

def test_v1_1_2_api_root(client):
    """Ensure root entry layout accurately reports full endpoint discovery maps."""
    response = client.get('/api/v1.1.2')
    assert response.status_code == 200
    data = response.get_json()
    assert data['version'] == "1.1.2"
    assert data['available_endpoints']['save_client'] == "POST /api/v1.1.2/save_client"


def test_v1_1_2_get_programs(client):
    """Verify version 1.1.2 list tracking handles function properly."""
    response = client.get('/api/v1.1.2/programs')
    assert response.status_code == 200
    assert "Beginner (BG)" in response.json['programs']


def test_v1_1_2_entire_plan_variant(client):
    """Verify version 1.1.2 specific variants parse profiles successfully."""
    response = client.get('/api/v1.1.2/entire_plan?program_name=Muscle Gain (MG)')
    assert response.status_code == 200
    assert "Squat, Bench" in response.json['weekly_workout_chart']


def test_v1_1_2_weekly_workout_chart_variant(client):
    response = client.get('/api/v1.1.2/weekly_workout_chart?program_name=Fat Loss (FL)')
    assert response.status_code == 200
    assert "Cardio, Bench" in response.json['weekly_workout_chart']


def test_v1_1_2_daily_nutrition_plan_variant(client):
    response = client.get('/api/v1.1.2/daily_nutrition_plan?program_name=Beginner (BG)')
    assert response.status_code == 200
    assert "Balanced Tamil Meals" in response.json['daily_nutrition_plan']


def test_v1_1_2_save_client_success(client):
    """Ensure validation records parse, transform fields, and append to the cache list."""
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


def test_v1_1_2_save_client_duplicate_error(client):
    """Ensures duplicate tracking conditions flag unique profiles case-insensitively."""
    payload = {
        "name": "Alex Smith",
        "program": "Beginner (BG)",
        "age": 24,
        "weight": 70,
        "progress": 80,
        "notes": "Testing duplicate intercept layers"
    }
    # Initial save registers cleanly
    resp1 = client.post('/api/v1.1.2/save_client', json=payload)
    assert resp1.status_code == 200

    # Repeating request with a matching string identity should be rejected
    payload["name"] = "alex smith"
    resp2 = client.post('/api/v1.1.2/save_client', json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json["error"]


def test_v1_1_2_save_client_validation_missing_fields(client):
    """Checks for 400 status parameters if required registration keys are empty."""
    payload = {"name": "", "program": "Fat Loss (FL)"}
    response = client.post('/api/v1.1.2/save_client', json=payload)
    assert response.status_code == 400
    assert "Please fill client name and program" in response.json["error"]


def test_v1_1_2_get_clients_list(client):
    """Verifies retrieval arrays track context entries sequentially."""
    # Seed a target record structure
    client.post('/api/v1.1.2/save_client', json={"name": "Jane", "program": "Fat Loss (FL)"})

    response = client.get('/api/v1.1.2/clients')
    assert response.status_code == 200
    assert len(response.json["clients"]) == 1
    assert response.json["clients"][0]["name"] == "Jane"


def test_v1_1_2_export_csv_empty_error_boundary(client):
    """Validates boundary error triggers if client attempts to parse empty metrics."""
    response = client.get('/api/v1.1.2/export_csv')
    assert response.status_code == 400
    assert "No clients to export" in response.json["error"]


def test_v1_1_2_export_csv_file_generation_stream(client):
    """Confirms text data formats match standard raw streaming configurations."""
    client.post('/api/v1.1.2/save_client', json={
        "name": "Jane", "program": "Fat Loss (FL)", "age": 28, "weight": 60, "progress": 95, "notes": "Elite tracking"
    })
    response = client.get('/api/v1.1.2/export_csv')
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert b"Name,Age,Weight,Program,Adherence,Notes" in response.data
    assert b"Jane,28,60.0,Fat Loss (FL),95,Elite tracking" in response.data


def test_v1_1_2_clear_clients_purge(client):
    """Ensures purgatory clear parameters return tracking arrays cleanly to baseline sizes."""
    client.post('/api/v1.1.2/save_client', json={"name": "Temp", "program": "Beginner (BG)"})
    response = client.post('/api/v1.1.2/clear_clients')
    assert response.status_code == 200

    # Confirm structural list array length has reverted down to zero
    resp_list = client.get('/api/v1.1.2/clients')
    assert len(resp_list.json["clients"]) == 0
