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

PROGRAMS = {
"Fat Loss (FL)": {"factor": 22},
            "Muscle Gain (MG)": {"factor": 35},
            "Beginner (BG)": {"factor": 26}
}
PROGRAMS_LOWER = {k.lower(): v for k, v in PROGRAMS.items()}

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
# FINAL REFINED ENDPOINTS OF v2 : V2.1.2
# ==========================================
@app.route("/api/v2.2.1", methods=["GET"])
def api_root():
    return jsonify({
        "version": "2.2.1",
        "status": "active",
        "service": "ACEest Fitness Foundation Engine",
        "available_endpoints": {
            "health_2_1_2": "GET /api/v2.1.2/health",
            "health": "GET /api/v2.1.2/health",
            "save_client": "POST /api/v2.1.2/client",
            "load_client": "GET /api/v2.1.2/client",
            "save_progress": "POST /api/v2.1.2/progress",
            "load_progress": "GET /api/v2.2.1/progress",
            "export_progress":"GET /api/v2.2.1/progress/export"
        }
    }), 200

"""Health Check V2.1.2"""
@app.route("/api/v2.1.2/health", methods=["GET"])
def health_check_2_1_2():
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "ACEest Fitness API V2.1.2 Backend",
            }
        ),
        200,
    )

@app.route("/api/v2.2.1/health", methods=["GET"])
def health_check():
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "ACEest Fitness API V2.2.1 Backend",
            }
        ),
        200,
    )

@app.route("/api/v2.1.2/client", methods=["POST"])
@app.route("/api/v2.2.1/client", methods=["POST"])
def save_client():
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

    program_details = PROGRAMS_LOWER.get(program.lower())
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


@app.route("/api/v2.1.2/client", methods=["GET"])
@app.route("/api/v2.2.1/client", methods=["GET"])
def load_client():
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

@app.route("/api/v2.1.2/progress", methods=["POST"])
@app.route("/api/v2.2.1/progress", methods=["POST"])
def save_progress():
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


# ==========================================
# NEWLY APPENDED PROGRESS ANALYTICS ENDPOINTS
# ==========================================

@app.route("/api/v2.2.1/progress", methods=["GET"])
def load_progress():
    ensure_db_initialized()
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Missing required 'name' filter parameter"}), 400

    try:
        with get_db_connection() as conn:
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


@app.route("/api/v2.2.1/progress/export", methods=["GET"])
def export_progress():
    """Generates an on-the-fly streaming RFC-compliant CSV document download."""
    ensure_db_initialized()
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Missing required 'name' filter parameter"}), 400

    try:
        with get_db_connection() as conn:
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



if __name__ == "__main__":
    port_number = 5000
    for arg in sys.argv:
        if arg.startswith('--port='):
            # FIX: Safely extracts the value after the '=' sign
            port_number = int(arg.split('=')[1])

    print(f"Launching ACEest Fitness Engine on port {port_number}")
    app.run(host='0.0.0.0', port=port_number, debug=False)
