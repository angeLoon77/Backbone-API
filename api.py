import os
from flask import Flask, jsonify, request
from online_database import register_user, login_user
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
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")