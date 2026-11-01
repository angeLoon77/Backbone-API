from flask import Flask, jsonify, request
from online_database import register_user

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

@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)