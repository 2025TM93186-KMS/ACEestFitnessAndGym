from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import sys
import io
import csv

import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Eliminates Cross-Origin blocking parameters for client integrations
CLIENTS_DB = []
DB_NAME = "aceest_fitness.db"

PROGRAMS_v1_0 = {
            "Fat Loss (FL)": {
                "workout": "Mon: 5x5 Back Squat + AMRAP\nTue: EMOM 20min Assault Bike\nWed: Bench Press + 21-15-9\nThu: 10RFT Deadlifts/Box Jumps\nFri: 30min Active Recovery",
                "diet": "B: 3 Egg Whites + Oats Idli\nL: Grilled Chicken + Brown Rice\nD: Fish Curry + Millet Roti\nTarget: 2,000 kcal",
                "color": "#e74c3c"
            },
            "Muscle Gain (MG)": {
                "workout": "Mon: Squat 5x5\nTue: Bench 5x5\nWed: Deadlift 4x6\nThu: Front Squat 4x8\nFri: Incline Press 4x10\nSat: Barbell Rows 4x10",
                "diet": "B: 4 Eggs + PB Oats\nL: Chicken Biryani (250g Chicken)\nD: Mutton Curry + Jeera Rice\nTarget: 3,200 kcal",
                "color": "#2ecc71"
            },
            "Beginner (BG)": {
                "workout": "Circuit Training: Air Squats, Ring Rows, Push-ups.\nFocus: Technique Mastery & Form (90% Threshold)",
                "diet": "Balanced Tamil Meals: Idli-Sambar, Rice-Dal, Chapati.\nProtein: 120g/day",
                "color": "#3498db"
            }
}

PROGRAMS_v1_1 = {
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

PROGRAMS_v1_1_2 = {
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
PROGRAMS_LOWER_v1_0 = {k.lower(): v for k, v in PROGRAMS_v1_0.items()}
PROGRAMS_LOWER_v1_1 = {k.lower(): v for k, v in PROGRAMS_v1_1.items()}
PROGRAMS_LOWER_v1_1_2 = {k.lower(): v for k, v in PROGRAMS_v1_1_2.items()}

PROGRAMS_v2_0_1 = {
"Fat Loss (FL)": {"factor": 22},
            "Muscle Gain (MG)": {"factor": 35},
            "Beginner (BG)": {"factor": 26}
}
PROGRAMS_LOWER_v2_0_1 = {k.lower(): v for k, v in PROGRAMS_v2_0_1.items()}

# V2.0.1 :
# ---------- DATABASE LOGIC (ISOLATED LAZY LOADING) ----------
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_db_initialized():
    """Checks and builds schemas only when invoked inside v2.0.1 data engines."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                age INTEGER,
                weight REAL,
                program TEXT,
                calories INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT,
                week TEXT,
                adherence INTEGER
            )
        """)
        conn.commit()

# ==========================================
# V1.0 ENDPOINTS
# ==========================================

"""Health Check V1.0"""
@app.route("/api/v1.0/health", methods=["GET"])
def health_check_v1_0():  # FIXED: Renamed to prevent override
    return jsonify({"status": "healthy", "service": "ACEest Fitness API V1.0 Backend"}), 200

@app.route("/api/v1.0", methods=["GET"])
def api_root_v1_0():
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
            "health_v1.0": "GET /api/v1.0/health",
            "entire_plan": "GET /api/v1.0/entire_plan",
            "weekly_workout_chart": "GET /api/v1.0/weekly_workout_chart",
            "daily_nutrition_plan": "GET /api/v1.0/daily_nutrition_plan"
        }
    }), 200

"""Returns a list of all available workout and fitness tracks"""
@app.route("/api/v1.0/programs", methods=["GET"])
def get_programs():
    return jsonify({"programs": list(PROGRAMS_v1_0.keys())}), 200

"""
    Returns full program details based on the program_name query parameter.
    Example: /api/v1.0/entire_plan?program_name=Fat Loss (FL)
"""
@app.route("/api/v1.0/entire_plan", methods=["GET"])
def get_entire_plan():
    program_name = request.args.get("program_name")
    if not program_name:
        return jsonify({"error": "Missing required 'program_name' query parameter"}), 400

    program = PROGRAMS_LOWER_v1_0.get(program_name.lower())
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

    program = PROGRAMS_LOWER_v1_0.get(program_name.lower())
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404

    return jsonify({"weekly_workout_chart": program.get("workout")}), 200

@app.route("/api/v1.0/daily_nutrition_plan", methods=["GET"])
def get_daily_nutrition_plan():
    program_name = request.args.get("program_name")
    if not program_name:
        return jsonify({"error": "Missing 'program_name' query parameter"}), 400

    program = PROGRAMS_LOWER_v1_0.get(program_name.lower())
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404

    return jsonify({"daily_nutrition_plan": program.get("diet")}), 200


# ==========================================
# V1.1 ENDPOINTS
# ==========================================
@app.route("/api/v1.1", methods=["GET"])
def api_root_v1_1():
    return jsonify({
        "version": "1.1",
        "status": "active",
        "service": "ACEest Fitness Foundation Engine",
        "available_endpoints": {
            "programs": "GET /api/v1.0/programs",
            "health_v1.0": "GET /api/v1.0/health",
            "health_v1.1": "GET /api/v1.1/health",
            "entire_plan": "GET /api/v1.0/entire_plan",
            "weekly_workout_chart": "GET /api/v1.0/weekly_workout_chart",
            "daily_nutrition_plan": "GET /api/v1.0/daily_nutrition_plan",
            "calculate_calories": "POST /api/v1.1/calculate_calories"
        }
    }), 200

"""Health Check V1.1"""
@app.route("/api/v1.1/health", methods=["GET"])
def health_check_v1_1():  # FIXED: Renamed to prevent override
    return jsonify({"status": "healthy", "service": "ACEest Fitness API V1.1 Backend"}), 200


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

    program = PROGRAMS_LOWER_v1_1.get(program_name.lower())
    if not program or weight <= 0:
        return jsonify({"calories": "--"})

    calories = int(weight * program["calorie_factor"])
    return jsonify({"calories": f"{calories} kcal"})


# ==========================================
# V1.1.2 ENDPOINTS
# ==========================================

@app.route("/api/v1.1.2", methods=["GET"])
def api_root_v1_1_2():
    return jsonify({
        "version": "1.1.2",
        "status": "active",
        "service": "ACEest Fitness Foundation Engine",
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
            "clear_clients": "DELETE /api/v1.1.2/clear_clients"
        }
    }), 200

"""Health Check V1.1.2"""
@app.route("/api/v1.1.2/health", methods=["GET"])
def health_check_v1_1_2():  # FIXED: Renamed to prevent override
    return jsonify({"status": "healthy", "service": "ACEest Fitness API V1.1.2 Backend"}), 200

"""Returns a list of all available workout tracks (v1.1.2 variant)"""
@app.route("/api/v1.1.2/programs", methods=["GET"])
def get_programs_v112():
    return jsonify({"programs": list(PROGRAMS_v1_1_2.keys())}), 200

"""Returns full program details (v1.1.2 variant)"""
@app.route("/api/v1.1.2/entire_plan", methods=["GET"])
def get_entire_plan_v112():
    program_name = request.args.get("program_name")
    if not program_name:
        return jsonify({"error": "Missing required 'program_name' query parameter"}), 400

    program = PROGRAMS_LOWER_v1_1_2.get(program_name.lower())
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

    program = PROGRAMS_LOWER_v1_1_2.get(program_name.lower())
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found"}), 404

    return jsonify({"weekly_workout_chart": program.get("workout")}), 200

@app.route("/api/v1.1.2/daily_nutrition_plan", methods=["GET"])
def get_daily_nutrition_plan_v112():
    program_name = request.args.get("program_name")
    if not program_name:
        return jsonify({"error": "Missing 'program_name' query parameter"}), 400

    program = PROGRAMS_LOWER_v1_1_2.get(program_name.lower())
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

    program = PROGRAMS_LOWER_v1_1_2.get(program_name.lower())
    if not program:
        return jsonify({"error": f"Program '{program_name}' not found."}), 400

    #if any(client['name'].lower() == name.lower() for client in CLIENTS_DB):
    #    return jsonify({"error": f"A client named '{name}' already exists."}), 400

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

@app.route("/api/v1.1.2/clear_clients", methods=["DELETE"])
def clear_clients():
    CLIENTS_DB.clear()
    return jsonify({"success": "In-memory database context cleared successfully."}), 200


# ==========================================
# V2.0.1 ENDPOINTS
# ==========================================
@app.route("/api/v2.0.1", methods=["GET"])
def api_root():
    return jsonify({
        "version": "2.0.1",
        "status": "active",
        "service": "ACEest Fitness Foundation Engine",
        "available_endpoints": {
            "programs": "GET /api/v1.0/programs",
            "health_v1.0": "GET /api/v1.0/health",
            "health_v1.1": "GET /api/v1.1/health",
            "health": "GET /api/v1.1.2/health",
            "entire_plan": "GET /api/v1.0/entire_plan",
            "weekly_workout_chart": "GET /api/v1.0/weekly_workout_chart",
            "daily_nutrition_plan": "GET /api/v1.0/daily_nutrition_plan",
            "calculate_calories": "POST /api/v1.1/calculate_calories",
            "save_client_v1.1.2": "POST /api/v1.1.2/save_client",
            "get_clients": "GET /api/v1.1.2/clients",
            "export_csv": "GET /api/v1.1.2/export_csv",
            "clear_clients": "DELETE /api/v1.1.2/clear_clients",
            "save_client_v2.0.1": "POST /api/v2.0.1/client",
            "load_client": "GET /api/v2.0.1/client",
            "save_progress": "POST /api/v2.0.1/progress"
        }
    }), 200

"""Health Check V2.0.1"""
@app.route("/api/v2.0.1/health", methods=["GET"])
def health_check_v2_0_1():
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "ACEest Fitness API V2.0.1 Backend",
            }
        ),
        200,
    )
#
    #Client and DB Related Operations
#
@app.route("/api/v2.0.1/client", methods=["POST"])
def save_client_v2_0_1():
    ensure_db_initialized()  # Auto-creates tables seamlessly if missing
    data = request.json or {}
    name = data.get("name")
    program = data.get("program")

    if not name or not program:
        return jsonify({"error": "Name and Program fields are required"}), 400

    try:
        age = int(data.get("age", 0))
        weight = float(data.get("weight", 0.0))
    except (ValueError, TypeError):
        return (
            jsonify({"error": "Invalid format for age or numerical weight"}),
            400,
        )

    program_details = PROGRAMS_LOWER_v2_0_1.get(program.lower())
    if not program_details:
        return jsonify({"error": f"Program '{program}' matches no baseline"}), 404

    calories = int(weight * program_details["factor"])

    try:
        with get_db_connection() as conn:
            client = conn.execute(
                """
                INSERT OR REPLACE INTO clients (name, age, weight, program, calories)
                VALUES (?, ?, ?, ?, ?)
            """,
                (name, age, weight, program, calories),
            )
            conn.commit()
        return (
            jsonify({"message": "Client data saved", "id":client.lastrowid, "calories": calories}),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v2.0.1/client", methods=["GET"])
def load_client_v2_0_1():
    ensure_db_initialized()  # Auto-creates tables seamlessly if missing
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Missing 'name' query parameter"}), 400

    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM clients WHERE name = ?", (name,)
            ).fetchone()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not row:
        return jsonify({"error": "Client not found"}), 404

    return (
        jsonify(
            {
                "id": row["id"],
                "name": row["name"],
                "age": row["age"],
                "weight": row["weight"],
                "program": row["program"],
                "calories": row["calories"],
            }
        ),
        200,
    )


@app.route("/api/v2.0.1/progress", methods=["POST"])
def save_progress_v2_0_1():
    ensure_db_initialized()  # Auto-creates tables seamlessly if missing
    data = request.json or {}
    name = data.get("name")

    if not name:
        return jsonify({"error": "Target client 'name' property required"}), 400

    try:
        adherence = int(data.get("adherence", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Adherence configuration must be numerical"}), 400

    week_stamp = datetime.now().strftime("Week %U - %Y")

    try:
        with get_db_connection() as conn:
            progress = conn.execute(
                """
                INSERT INTO progress (client_name, week, adherence)
                VALUES (?, ?, ?)
            """,
                (name, week_stamp, adherence),
            )
            conn.commit()
        return (
            jsonify({"message": "Weekly progress logged", "id": progress.lastrowid}),
            201,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    port_number = 5000
    for arg in sys.argv:
        if arg.startswith('--port='):
            # FIX: Safely extracts the value after the '=' sign
            port_number = int(arg.split('=')[1])

    print(f"Launching ACEest Fitness Engine on port {port_number}")
    app.run(host='0.0.0.0', port=port_number, debug=False)
