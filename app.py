from flask import Flask, jsonify, request
from flask_cors import CORS
import sys

app = Flask(__name__)
CORS(app)  # Eliminates Cross-Origin blocking parameters for client integrations

PROGRAMS = {
    "Fat Loss (FL)": {
        "workout": (
            "Mon: Back Squat 5x5 + Core\n"
            "Tue: EMOM 20min Assault Bike\n"
            "Wed: Bench Press + 21-15-9\n"
            "Thu: Deadlift + Box Jumps\n"
            "Fri: Zone 2 Cardio 30min"
        ),
        "diet": (
            "Breakfast: Egg Whites + Oats\n"
            "Lunch: Grilled Chicken + Brown Rice\n"
            "Dinner: Fish Curry + Millet Roti\n"
            "Target: ~2000 kcal"
        ),
        "color": "#e74c3c",
        "calorie_factor": 22
    },
    "Muscle Gain (MG)": {
        "workout": (
            "Mon: Squat 5x5\n"
            "Tue: Bench 5x5\n"
            "Wed: Deadlift 4x6\n"
            "Thu: Front Squat 4x8\n"
            "Fri: Incline Press 4x10\n"
            "Sat: Barbell Rows 4x10"
        ),
        "diet": (
            "Breakfast: Eggs + Peanut Butter Oats\n"
            "Lunch: Chicken Biryani\n"
            "Dinner: Mutton Curry + Rice\n"
            "Target: ~3200 kcal"
        ),
        "color": "#2ecc71",
        "calorie_factor": 35
    },
    "Beginner (BG)": {
        "workout": (
            "Full Body Circuit:\n"
            "- Air Squats\n"
            "- Ring Rows\n"
            "- Push-ups\n"
            "Focus: Technique & Consistency"
        ),
        "diet": (
            "Balanced Tamil Meals\n"
            "Idli / Dosa / Rice + Dal\n"
            "Protein Target: 120g/day"
        ),
        "color": "#3498db",
        "calorie_factor": 26
    }
}

# For lowercase mapping
PROGRAMS_LOWER = {k.lower(): v for k, v in PROGRAMS.items()}


# ==========================================
# V1.0 ENDPOINTS
# ==========================================

@app.route("/api/v1.0", methods=["GET"])
def api_root():
    return jsonify({
        "version": "1.0",
        "status": "active",
        "service": "ACEest Fitness Foundation Engine",
        "metrics_summary": {
            "capacity_users": 150,
            "area_sq_ft": 10000,
            "break_even_members": 250
        },
        "available_endpoints": {
            "programs": "GET /api/v1.0/programs",
            "health": "GET /api/v1.0/health",
            "entire_plan": "GET /api/v1.0/entire_plan",
            "weekly_workout_chart": "GET /api/v1.0/weekly_workout_chart",
            "daily_nutrition_plan": "GET /api/v1.0/daily_nutrition_plan",
            "calculate_calories": "POST /api/v1.1/calculate_calories",
            "save_client": "POST /api/v1.1/save_client"
        }
    }), 200

"""Health Check"""
@app.route("/api/v1.0/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "ACEest Fitness API V1.0 Backend"}), 200

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
# NEW V1.1 ENDPOINTS
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

"""
    Validates profile metrics processing data structures in-memory.
    POST JSON payload: {"name": "Jane", "program": "Muscle Gain (MG)", "age": 25, "weight": 70, "progress": 90}
"""
@app.route("/api/v1.1/save_client", methods=["POST"])
def save_client():
    data = request.json or {}
    name = data.get("name", "").strip()
    program_name = data.get("program")

    if not name or not program_name:
        return jsonify({"error": "Please fill client name and program."}), 400

    program = PROGRAMS_LOWER.get(program_name.lower())
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found."}), 400

    try:
        age = int(data.get("age", 0))
        weight = float(data.get("weight", 0))
        target_adherence = int(data.get("progress", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid format for numeric metrics."}), 400

    calories = int(weight * program["calorie_factor"]) if weight > 0 else 0

    return jsonify({
        "success": f"Client '{name}' validated and processed successfully.",
        "adherence": target_adherence,
        "calculated_calories": calories
    }), 200


if __name__ == "__main__":
    port_number = 5000
    for arg in sys.argv:
        if arg.startswith('--port='):
            # FIX: Safely extracts the value after the '=' sign
            port_number = int(arg.split('=')[1])

    print(f"Launching ACEest Fitness Engine on port {port_number}")
    app.run(host='0.0.0.0', port=port_number, debug=False)
