from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import sys
import io
import csv

import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Eliminates Cross-Origin blocking parameters for client integrations

DB_NAME = "aceest_fitness.db"

# ==========================================
# V3.0.1
# ==========================================
PROGRAMS = {
            "Fat Loss (FL) – 3 day": {"factor": 22, "desc": "3-day full-body fat loss"},
            "Fat Loss (FL) – 5 day": {"factor": 24, "desc": "5-day split, higher volume fat loss"},
            "Muscle Gain (MG) – PPL": {"factor": 35, "desc": "Push/Pull/Legs hypertrophy"},
            "Beginner (BG)": {"factor": 26, "desc": "3-day simple beginner full-body"},
        }
PROGRAMS_LOWER = {k.lower(): v for k, v in PROGRAMS.items()}


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='clients'"
            )
            exists = cur.fetchone() is not None

            if exists:
                # Check schema
                cur.execute("PRAGMA table_info(clients)")
                cols = [row[1] for row in cur.fetchall()]
                required = {
                    "id",
                    "name",
                    "age",
                    "height",
                    "weight",
                    "program",
                    "calories",
                    "target_weight",
                    "target_adherence",
                }
                if not required.issubset(set(cols)):
                    # Drop and recreate with full schema
                    cur.execute("DROP TABLE clients")

            # Create clients with full schema
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    age INTEGER,
                    height REAL,
                    weight REAL,
                    program TEXT,
                    calories INTEGER,
                    target_weight REAL,
                    target_adherence INTEGER
                )
                """
            )

            # Weekly adherence
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT,
                    week TEXT,
                    adherence INTEGER
                )
                """
            )

            # Workouts (session-level)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS workouts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT,
                    date TEXT,
                    workout_type TEXT,
                    duration_min INTEGER,
                    notes TEXT
                )
                """
            )

            # Exercises (per workout)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS exercises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workout_id INTEGER,
                    name TEXT,
                    sets INTEGER,
                    reps INTEGER,
                    weight REAL
                )
                """
            )

            # Body metrics (weight, waist, etc.)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT,
                    date TEXT,
                    weight REAL,
                    waist REAL,
                    bodyfat REAL
                )
                """
            )
            conn.commit()
    finally:
        conn.close()

init_db()
@app.route("/api/v3.0.1", methods=["GET"])
def api_root():
    return jsonify({
        "version": "3.0.1",
        "status": "active",
        "service": "ACEest Fitness Foundation Engine",
        "available_endpoints": {
            "health": "GET /api/v3.0.1/health",
            "save_progress": "POST /api/v3.0.1/progress",
            "load_progress": "GET /api/v3.0.1/progress",
            "export_progress":"GET /api/v3.0.1/progress/export",
            "save_client": "POST /api/v3.0.1/client",
            "load_client": "GET /api/v3.0.1/client",
            "show_weight_chart": "GET /api/v3.0.1/weight",
            "show_bmi_info": "GET /api/v3.0.1/bmi",
            "save_workout": "POST /api/v3.0.1/workout",
            "save_metrics": "POST /api/v3.0.1/metrics",
            "workout_history": "GET /api/v3.0.1/workout",
        }
    }), 200

# region V3.0.1
# ==========================================
# V3.0.1
# ==========================================
@app.route("/api/v3.0.1/health", methods=["GET"])
def health_check():
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "ACEest Fitness API V3.0.1 Backend",
            }
        ),
        200,
    )
@app.route("/api/v3.0.1/client", methods=["POST"])
def save_client():
        try:
            data = request.json or {}
            name = data.get("name")
            program = data.get("program")
            if not name or not program:
                return jsonify({"error": "Name and Program fields are required"}), 400

            age = int(data.get("age", 0))
            weight = float(data.get("weight", 0.0))
            height = float(data.get("height", 0.0))
            target_weight = float(data.get("target_weight", 0.0))
            target_adherence = float(data.get("target_adherence", 0.0))

            program_details = PROGRAMS_LOWER.get(program.lower())
            if not program_details:
                return jsonify({"error": f"Program '{program}' matches no baseline"}), 404

            calories = int(weight * program_details["factor"])

            program_value = next(
                (key for key, val in PROGRAMS.items() if key.lower() == program.lower()),
                program  # Default string fallback value if no match is found
            )

            init_db()
            with get_db() as conn:
                cur = conn.cursor()
                client = cur.execute(
                """
                INSERT OR REPLACE INTO clients
                (name, age, height, weight, program, calories, target_weight, target_adherence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                        name,
                        age,
                        height,
                        weight,
                        program_value,
                        calories,
                        target_weight,
                        target_adherence,
                    ),
                )
                conn.commit()
                return (
                    jsonify({"message": "Client data saved", "id": client.lastrowid, "calories": calories}),
                    200,
                )
        except Exception as e:
            return jsonify({"error": str(e)}), 500
@app.route("/api/v3.0.1/client", methods=["GET"])
def load_client():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400

        init_db()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clients WHERE name=?", (name,))
            client = cur.fetchone()
            if not client:
                return jsonify({"error": "Client not found"}), 404
            target_weight = client["target_weight"]
            target_adherence = client["target_adherence"]
            program = client["program"]
            # ------------------
            cur.execute(
                "SELECT COUNT(*), AVG(adherence) FROM progress WHERE client_name=?",
                (name,),
            )
            total_weeks, avg_adherence = cur.fetchone()
            avg_adherence = round(avg_adherence, 1) if avg_adherence is not None else 0
            #------------------
            cur.execute(
                "SELECT date, weight, waist, bodyfat FROM metrics WHERE client_name=? ORDER BY date DESC LIMIT 1",
                (name,),
            )
            last_metric = cur.fetchone()

            last_metric_str = "None"
            if last_metric:
                m_date, m_weight, m_waist, m_bodyfat = last_metric
                last_metric_str = (
                    f"{m_date} | {m_weight} kg, Waist {m_waist} cm, "
                    f"Bodyfat {m_bodyfat}%"
                )
            # ------------------
            goal_summary = "None"
            if target_weight or target_adherence:
                goal_summary = ""
                if target_weight:
                    goal_summary += f"Target Weight: {target_weight} kg; "
                if target_adherence:
                    goal_summary += f"Target Adherence: {target_adherence}%"

            prog_desc = program #programs.get(program, {}).get("desc", "")

            return jsonify({
                "CLIENT PROFILE": {
                    "id": client["id"],
                    "name": client["name"],
                    "age": client["age"],
                    "height": f"{client['height']} cm" if client['height'] else "-",
                    "weight": f"{client['weight']} kg" if client['weight'] else "-",
                    "program": program,
                    "calories": f"{client['calories']} kcal/day",
                    "target_weight": target_weight,
                    "target_adherence": target_adherence
                },
                "PROGRAM NOTES": {
                    "description": prog_desc
                },
                "GOALS": {
                    "summary": goal_summary
                },
                "PROGRESS SUMMARY": {
                    "Weeks logged": total_weeks,
                    "Average adherence": f"{avg_adherence}%"
                },
                "LAST BODY METRICS": {
                    "summary": last_metric_str
                }
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/v3.0.1/progress", methods=["POST"])
def save_progress():
    try:
        data = request.json or {}
        name = data.get("name")
        if not name:
            return jsonify({"error": "Target client 'name' property required"}), 400
        adherence = int(data.get("adherence", 0))
        week_stamp = datetime.now().strftime("Week %U - %Y")
        init_db()
        with get_db() as conn:
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
@app.route("/api/v3.0.1/progress", methods=["GET"])
def load_progress():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing required 'name' filter parameter"}), 400
        init_db()
        with get_db() as conn:
            rows = conn.execute("""
                SELECT id, week, adherence 
                FROM progress 
                WHERE client_name = ? 
                ORDER BY id ASC
            """, (name,)).fetchall()
            progress_log = [
                {"id": row["id"], "week": row["week"], "adherence": row["adherence"]}
                for row in rows
            ]
            return jsonify({"client_name": name, "progress": progress_log}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/v3.0.1/progress/export", methods=["GET"])
def export_progress():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing required 'name' filter parameter"}), 400
        init_db()
        with get_db() as conn:
            rows = conn.execute("""
                SELECT week, adherence 
                FROM progress 
                WHERE client_name = ? 
                ORDER BY id ASC
            """, (name,)).fetchall()
            if not rows:
                return jsonify({"error": f"No structural timelines logged for {name}"}), 404
            output = io.StringIO()
            # noinspection PyTypeChecker
            writer = csv.writer(output, delimiter=",", quoting=csv.QUOTE_MINIMAL)

            # Write CSV Schema Headers
            writer.writerow(["Client Name", "Week Identifier", "Adherence Percentage"])
            for row in rows:
                writer.writerow([name, row["week"], f"{row['adherence']}%"])

            response_stream = output.getvalue()
            output.close()

            # Build streaming response configuration headers
            filename = f"{name.lower().replace(' ', '_')}_progress.csv"
            return Response(
                response_stream,
                mimetype="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/v3.0.1/weight", methods=["GET"])
def show_weight_chart():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing required 'name' filter parameter"}), 400

        init_db()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT date, weight
                FROM metrics
                WHERE client_name=? AND weight IS NOT NULL
                ORDER BY date
                """,
                (name,),
            )
            data = cur.fetchall()
            if not data:
                return jsonify({"error": "No weight metrics available for this client"}), 404

            return jsonify({"client_name": name, "weight_chart": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/v3.0.1/bmi", methods=["GET"])
def show_bmi_info():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing required 'name' filter parameter"}), 400

        init_db()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clients WHERE name=?", (name,))
            client = cur.fetchone()
            if not client:
                return jsonify({"error": "Client not found"}), 404
            height = client["height"]
            weight = client["weight"]

            if height <= 0 or weight <= 0:
                return jsonify({"error", "Missing Data, Enter valid height and weight first"})
            h_m = height / 100.0
            bmi = weight / (h_m * h_m)
            bmi = round(bmi, 1)

            if bmi < 18.5:
                category = "Underweight"
                risk = "Potential nutrient deficiency, low energy."
            elif bmi < 25:
                category = "Normal"
                risk = "Low risk if active and strong."
            elif bmi < 30:
                category = "Overweight"
                risk = "Moderate risk; focus on adherence and progressive activity."
            else:
                category = "Obese"
                risk = "Higher risk; prioritize fat loss, consistency, and supervision."
            return jsonify({"BMI Info":
                    f"BMI for {name}: {bmi} ({category})\n\nRisk note: {risk}"
            }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/v3.0.1/metrics", methods=["POST"])
def save_metrics():
        try:
            data = request.json or {}
            name = data.get("name")
            if not name or not data.get("date"):
                return jsonify({"error": "Name and Date fields are required"}), 400

            date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
            m_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            m_weight = float(data.get("weight", 0.0))
            m_waist = float(data.get("waist", 0.0))
            m_bf = float(data.get("body_fat", 0.0))

            init_db()
            with get_db() as conn:
                cur = conn.cursor()
                metrics = cur.execute(
                    """
                    INSERT INTO metrics (client_name, date, weight, waist, bodyfat)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, m_date, m_weight, m_waist, m_bf),
                )
                conn.commit()
            return (
                jsonify({"message": "Metrics logged successfully", "id": metrics.lastrowid}),
                200,
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500
@app.route("/api/v3.0.1/workout", methods=["POST"])
def save_workout():
        try:
            data = request.json or {}
            name = data.get("name")
            workout_type = ["Strength", "Hypertrophy", "Conditioning", "Mixed", "Mobility"]
            w_type = data.get("workout")
            #program = data.get("program")
            if not w_type.lower() in [w.lower() for w in workout_type]:
                return jsonify({"error": "Workout not found"}), 404
            if not name or not w_type:
                return jsonify({"error": "Name and Workout fields are required"}), 400

            date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
            w_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            duration = float(data.get("duration", 0.0))
            notes = data.get("notes", "")

            ex_name = data.get("ex_name", "")
            ex_sets = float(data.get("ex_sets", 0.0))
            ex_reps = float(data.get("ex_reps", 0.0))
            ex_weight = float(data.get("ex_weight", 0.0))

            init_db()
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO workouts (client_name, date, workout_type, duration_min, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, w_date, w_type, duration, notes),
                )
                workout_id = cur.lastrowid

                if ex_name:
                    cur.execute(
                        """
                        INSERT INTO exercises (workout_id, name, sets, reps, weight)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (workout_id, ex_name, ex_sets, ex_reps, ex_weight),
                    )

                conn.commit()
                return (
                    jsonify({"message": "Workout logged successfully", "id": workout_id}),
                    200,
                )
        except Exception as e:
            return jsonify({"error": str(e)}), 500
@app.route("/api/v3.0.1/workout", methods=["GET"])
def workout_history():
    try:
        name = request.args.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400
        init_db()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clients WHERE name=?", (name,))
            client = cur.fetchone()
            if not client:
                return jsonify({"error": "Client not found"}), 404
            # ------------------
            cur.execute(
                """
                SELECT date, workout_type, duration_min, notes
                FROM workouts
                WHERE client_name=?
                ORDER BY date DESC, id DESC
                """,
                (name,),
            )
            workouts = cur.fetchall()
            return (
                jsonify({"workout history": workouts}),
                200,
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# endregion


if __name__ == "__main__":
    port_number = 5000
    for arg in sys.argv:
        if arg.startswith('--port='):
            # FIX: Safely extracts the value after the '=' sign
            port_number = int(arg.split('=')[1])

    print(f"Launching ACEest Fitness Engine on port {port_number}")
    app.run(host='0.0.0.0', port=port_number, debug=False)
