from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import sys
import io
import csv

app = Flask(__name__)
CORS(app)  # Eliminates Cross-Origin blocking parameters for client integrations
CLIENTS_DB = []

PROGRAMS = {
    "Fat Loss (FL)": {"workout": "Back Squat, Cardio, Bench, Deadlift, Recovery",
                      "diet": "Egg Whites, Chicken, Fish Curry",
                      "color": "#e74c3c", "calorie_factor": 22},
    "Muscle Gain (MG)": {"workout": "Squat, Bench, Deadlift, Press, Rows",
                         "diet": "Eggs, Biryani, Mutton Curry",
                         "color": "#2ecc71", "calorie_factor": 35},
    "Beginner (BG)": {"workout": "Air Squats, Ring Rows, Push-ups",
                      "diet": "Balanced Tamil Meals",
                      "color": "#3498db", "calorie_factor": 26}
}

# For lowercase mapping
PROGRAMS_LOWER = {k.lower(): v for k, v in PROGRAMS.items()}

# ==========================================
# V1.0 ENDPOINTS
# ==========================================

"""Health Check V1.0"""
@app.route("/api/v1.0/health", methods=["GET"])
def health_check_v1_0():  # FIXED: Renamed to prevent override
    return jsonify({"status": "healthy", "service": "ACEest Fitness API V1.0 Backend"}), 200

"""Health Check V1.1"""
@app.route("/api/v1.1/health", methods=["GET"])
def health_check_v1_1():  # FIXED: Renamed to prevent override
    return jsonify({"status": "healthy", "service": "ACEest Fitness API V1.1 Backend"}), 200

"""Health Check V1.1.2"""
@app.route("/api/v1.1.2/health", methods=["GET"])
def health_check_v1_1_2():  # FIXED: Renamed to prevent override
    return jsonify({"status": "healthy", "service": "ACEest Fitness API V1.1.2 Backend"}), 200

"""Returns a list of all available workout and fitness tracks"""
@app.route("/api/v1.0/programs", methods=["GET"])
def get_programs():
    return jsonify({"programs": list(PROGRAMS.keys())}), 200

"""
    Returns full program details based on the program_name query parameter.
    Example: /api/v1.0/entire_plan?program_name=Fat Loss (FL)
"""
@app.route("/api/v1.0/entire_plan", methods=["GET"])
def get_entire_plan():
    program_name = request.args.get("program_name")
    if not program_name:
        return jsonify({"error": "Missing required 'program_name' query parameter"}), 400

    program = PROGRAMS_LOWER.get(program_name.lower())
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404

    return jsonify({
        "program_name": program_name,
        "ui_color": program.get("color"),
        "weekly_workout_chart": program.get("workout"),
        "daily_nutrition_plan": program.get("diet")
    }), 200

@app.route("/api/v1.0/weekly_workout_chart", methods=["GET"])
def get_weekly_workout_chart():
    program_name = request.args.get("program_name")
    if not program_name:
        return jsonify({"error": "Missing 'program_name' query parameter"}), 400

    program = PROGRAMS_LOWER.get(program_name.lower())
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404

    return jsonify({"weekly_workout_chart": program.get("workout")}), 200

@app.route("/api/v1.0/daily_nutrition_plan", methods=["GET"])
def get_daily_nutrition_plan():
    program_name = request.args.get("program_name")
    if not program_name:
        return jsonify({"error": "Missing 'program_name' query parameter"}), 400

    program = PROGRAMS_LOWER.get(program_name.lower())
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404

    return jsonify({"daily_nutrition_plan": program.get("diet")}), 200


# ==========================================
# V1.1 ENDPOINTS
# ==========================================

@app.route("/api/v1.1/calculate_calories", methods=["POST"])
def calculate_calories():
    data = request.json or {}
    program_name = data.get("program")
    try:
        weight = float(data.get("weight", 0))
    except (ValueError, TypeError):
        weight = 0.0

    if not program_name:
        return jsonify({"calories": "--"})

    program = PROGRAMS_LOWER.get(program_name.lower())
    if not program or weight <= 0:
        return jsonify({"calories": "--"})

    calories = int(weight * program["calorie_factor"])
    return jsonify({"calories": f"{calories} kcal"})


# ==========================================
# V1.1.2 ENDPOINTS
# ==========================================

@app.route("/api/v1.1.2", methods=["GET"])
def api_root():
    return jsonify({
        "version": "1.1.2",
        "status": "active",
        "service": "ACEest Fitness Foundation Engine",
        "metrics_summary": {
            "capacity_users": 150,
            "area_sq_ft": 10000,
            "break_even_members": 250
        },
        "available_endpoints": {
            "programs": "GET /api/v1.0/programs",
            "health_v1.0": "GET /api/v1.0/health",
            "health_v1.1": "GET /api/v1.1/health",
            "health": "GET /api/v1.1.2/health",
            "entire_plan": "GET /api/v1.0/entire_plan",
            "weekly_workout_chart": "GET /api/v1.0/weekly_workout_chart",
            "daily_nutrition_plan": "GET /api/v1.0/daily_nutrition_plan",
            "calculate_calories": "POST /api/v1.1/calculate_calories",
            "save_client": "POST /api/v1.1.2/save_client",
            "get_clients": "GET /api/v1.1.2/clients",
            "export_csv": "GET /api/v1.1.2/export_csv",
            "clear_clients": "POST /api/v1.1.2/clear_clients"
        }
    }), 200

"""Returns a list of all available workout tracks (v1.1.2 variant)"""
@app.route("/api/v1.1.2/programs", methods=["GET"])
def get_programs_v112():
    return jsonify({"programs": list(PROGRAMS.keys())}), 200

"""Returns full program details (v1.1.2 variant)"""
@app.route("/api/v1.1.2/entire_plan", methods=["GET"])
def get_entire_plan_v112():
    program_name = request.args.get("program_name")
    if not program_name:
        return jsonify({"error": "Missing required 'program_name' query parameter"}), 400

    program = PROGRAMS_LOWER.get(program_name.lower())
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404

    return jsonify({
        "program_name": program_name,
        "ui_color": program.get("color"),
        "weekly_workout_chart": program.get("workout"),
        "daily_nutrition_plan": program.get("diet")
    }), 200

@app.route("/api/v1.1.2/weekly_workout_chart", methods=["GET"])
def get_weekly_workout_chart_v112():
    program_name = request.args.get("program_name")
    if not program_name:
        return jsonify({"error": "Missing 'program_name' query parameter"}), 400

    program = PROGRAMS_LOWER.get(program_name.lower())
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404

    return jsonify({"weekly_workout_chart": program.get("workout")}), 200

@app.route("/api/v1.1.2/daily_nutrition_plan", methods=["GET"])
def get_daily_nutrition_plan_v112():
    program_name = request.args.get("program_name")
    if not program_name:
        return jsonify({"error": "Missing 'program_name' query parameter"}), 400

    program = PROGRAMS_LOWER.get(program_name.lower())
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404

    return jsonify({"daily_nutrition_plan": program.get("diet")}), 200

"""Validates and stores client data in-memory"""
@app.route("/api/v1.1.2/save_client", methods=["POST"])
def save_client():
    data = request.json or {}
    name = data.get("name", "").strip()
    program_name = data.get("program")

    if not name or not program_name:
        return jsonify({"error": "Please fill client name and program."}), 400

    program = PROGRAMS_LOWER.get(program_name.lower())
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found."}), 400

    if any(client['name'].lower() == name.lower() for client in CLIENTS_DB):
        return jsonify({"error": f"A client named '{name}' already exists."}), 400

    try:
        age = int(data.get("age", 0))
        weight = float(data.get("weight", 0))
        target_adherence = int(data.get("progress", 0))
        notes = data.get("notes", "").strip()
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid format for numeric metrics."}), 400

    client_record = {
        "name": name,
        "age": age,
        "weight": weight,
        "program": program_name,
        "adherence": target_adherence,
        "notes": notes
    }

    CLIENTS_DB.append(client_record)
    return jsonify({
        "success": f"Client '{name}' validated and processed successfully.",
        "client_summary": client_record
    }), 200

"""Retrieves the array of all stored clients"""
@app.route("/api/v1.1.2/clients", methods=["GET"])
def get_clients():
    return jsonify({"clients": CLIENTS_DB}), 200

"""Dynamically generated CSV text object"""
@app.route("/api/v1.1.2/export_csv", methods=["GET"])
def export_csv():
    if not CLIENTS_DB:
        return jsonify({"error": "No clients to export."}), 400

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Name", "Age", "Weight", "Program", "Adherence", "Notes"])

    for client in CLIENTS_DB:
        cw.writerow([
            client["name"], client["age"], client["weight"],
            client["program"], client["adherence"], client["notes"]
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=aceest_clients.csv"}
    )

@app.route("/api/v1.1.2/clear_clients", methods=["POST"])
def clear_clients():
    CLIENTS_DB.clear()
    return jsonify({"success": "In-memory database context cleared successfully."}), 200


if __name__ == "__main__":
    port_number = 5000
    for arg in sys.argv:
        if arg.startswith('--port='):
            # FIX: Safely extracts the value after the '=' sign
            port_number = int(arg.split('=')[1])

    print(f"Launching ACEest Fitness Engine on port {port_number}")
    app.run(host='0.0.0.0', port=port_number, debug=False)
