import os
import sys
from flask import Flask, jsonify
from supabase import create_client, Client

# Initialize the Flask web application
app = Flask(__name__)

print("Initializing Supabase client...")

# Get the Supabase credentials from environment variables
# This is the secure way to handle secrets.
try:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_KEY")
    supabase: Client = create_client(url, key)
except Exception as e:
    print(f"FATAL: Could not initialize Supabase client. Check ENV VARS.")
    print(f"Details: {e}")
    # We exit here because the app is useless if it can't connect.
    sys.exit(1)

# The table we are interacting with
TABLE_NAME = 'keep_alive_pings'

# This is the main endpoint that the external service will hit.
@app.route('/ping')
def keep_alive_ping():
    print("Received a /ping request. Interacting with Supabase...")
    try:
        # 1. INSERT a new row to generate activity
        print(f"Inserting a row into '{TABLE_NAME}'...")
        insert_response = supabase.table(TABLE_NAME).insert({}).execute()

        if len(insert_response.data) > 0:
            new_id = insert_response.data[0]['id']
            print(f"Successfully inserted row with ID: {new_id}")

            # 2. DELETE the exact same row immediately
            print(f"Deleting the row with ID: {new_id}...")
            supabase.table(TABLE_NAME).delete().eq('id', new_id).execute()
            print("Successfully deleted the row.")
            
            # Return a success message
            return jsonify({"status": "success", "message": f"Ping successful. Row {new_id} created and deleted."}), 200
        else:
            print(f"Error: Insert operation failed. API Error: {insert_response.error.message if insert_response.error else 'Unknown'}")
            return jsonify({"status": "error", "message": "Insert operation failed."}), 500

    except Exception as e:
        print(f"An unexpected error occurred during ping: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# A simple root endpoint to confirm the service is running
@app.route('/')
def index():
    return "Supabase Pinger web service is alive.", 200

# This part is only for local testing, Render uses Gunicorn
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))