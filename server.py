from flask import Flask, request, jsonify
from flask_socketio import SocketIO
import mysql.connector
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DB_CONFIG = {
    "host": "127.0.0.1", #192.168.100.174
    "port": 3307,
    "user": "root",
    "password": "",
    "database": "wfh_app",
    "use_pure": True
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@app.route("/login", methods=["POST"])
def login():
    print("Login request data:", request.json)  # debug
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing username/password"}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, username, name, status FROM users WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return jsonify(user)
    return jsonify({"error": "Invalid login"}), 401

@socketio.on("connect")
def handle_connect():
    print("Client connected")

@socketio.on("update_status")
def handle_status(data):
    try:
        user_id = int(data.get("user_id"))
        status = data.get("status", "offline")
        checked_in = bool(data.get("checked_in", False))
        in_call = bool(data.get("in_call", False))
        last_activity = datetime.now()

        conn = get_db()
        # update user
        update_cursor = conn.cursor()
        update_cursor.execute("""
            UPDATE users
            SET status=%s, checked_in=%s, in_call=%s, last_activity=%s
            WHERE id=%s
        """, (status, checked_in, in_call, last_activity, user_id))
        conn.commit()
        update_cursor.close()

        # fetch all users
        select_cursor = conn.cursor(dictionary=True)
        select_cursor.execute("SELECT id, name, status FROM users")
        users = select_cursor.fetchall()
        select_cursor.close()
        conn.close()

        # broadcast
        socketio.emit("status_update", users)

    except Exception as e:
        print("Error in handle_status:", e)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)