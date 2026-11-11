import os
import datetime
from flask import Flask, jsonify, request
from online_database import (
    register_user, login_user, get_prs, add_pr, delete_pr, get_exercises,
    get_prs_by_muscle_group, delete_prs_by_exercise,
)
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer, BadSignature

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not found on .env")

serializer = URLSafeTimedSerializer(SECRET_KEY)
TOKEN_MAX_AGE = 60 * 60 * 24  # 1 day in seconds

def create_token(user_id):
    return serializer.dumps(user_id)

def get_user_id_from_request():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    token = header[len("Bearer "):]
    try:
        return serializer.loads(token, max_age=TOKEN_MAX_AGE)
    except BadSignature:
        return None

app = Flask(__name__)

@app.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "Invalid input: username and password must be strings"}), 400
    if len(username.strip()) < 3 or len(password) < 6:
        return jsonify({"error": "Invalid input: Username needs 3+ characters and Password 6+"}), 400
    try:
        user_id = register_user(username, password)
    except ValueError as e:
        return jsonify({"error": str(e)}), 409

    return jsonify({"user_id": user_id}), 201

@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "Invalid input: username and password must be strings"}), 400
    user_id = login_user(username, password)
    if user_id is None:
        return jsonify({"error": "Invalid username or password"}), 401

    return jsonify({"token": create_token(user_id)}), 200

@app.get("/exercises")
def list_exercises():
    user_id = get_user_id_from_request()
    if user_id is None:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_exercises()), 200

@app.get("/prs")
def list_prs():
    user_id = get_user_id_from_request()
    if user_id is None:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(get_prs(user_id)), 200

@app.get("/prs/group/<muscle_group>")
def list_prs_by_group(muscle_group):
    user_id = get_user_id_from_request()
    if user_id is None:
        return jsonify({"error": "Unauthorized"}), 401
    rows = get_prs_by_muscle_group(user_id, muscle_group)
    return jsonify([
        {"name": name, "weight": weight, "reps": reps, "date": date.isoformat()}
        for name, weight, reps, date in rows
    ]), 200

@app.post("/prs")
def create_pr():
    user_id = get_user_id_from_request()
    if user_id is None:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    exercise_id = data.get("exercise_id")
    weight = data.get("weight")
    reps = data.get("reps")
    date = data.get("date") or datetime.date.today().isoformat()
    if not isinstance(date, str):
        return jsonify({"error": "date must be a string (YYYY-MM-DD)"}), 400

    if not isinstance(exercise_id, int) or not isinstance(reps, int):
        return jsonify({"error": "exercise_id and reps must be integers"}), 400
    if not isinstance(weight, (int, float)):
        return jsonify({"error": "weight must be a number"}), 400
    if weight < 0 or reps <= 0 or reps > 99:
        return jsonify({"error": "weight must be 0 or more and reps between 1 and 99"}), 400

    try:
        pr_id = add_pr(user_id, exercise_id, weight, reps, date)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"pr_id": pr_id}), 201

@app.delete("/prs/<int:pr_id>")
def remove_pr(pr_id):
    user_id = get_user_id_from_request()
    if user_id is None:
        return jsonify({"error": "Unauthorized"}), 401
    if not delete_pr(pr_id, user_id):
        return jsonify({"error": "PR not found"}), 404
    return jsonify({"deleted": True}), 200

@app.delete("/exercises/<int:exercise_id>/prs")
def remove_prs_by_exercise(exercise_id):
    user_id = get_user_id_from_request()
    if user_id is None:
        return jsonify({"error": "Unauthorized"}), 401
    deleted = delete_prs_by_exercise(user_id, exercise_id)
    return jsonify({"deleted": deleted}), 200


@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/me")
def me():
    user_id = get_user_id_from_request()
    if user_id is None:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"user_id": user_id}), 200


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG") == "1"
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug)