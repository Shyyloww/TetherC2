# keep_alive.py
import os
import sys
from supabase import create_client, Client

print("Starting Supabase keep-alive script...")

# Get the Supabase credentials from environment variables on Render
# This is the secure way to handle secrets.
try:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_KEY")
    supabase: Client = create_client(url, key)
except Exception as e:
    print(f"Error: Could not read environment variables or initialize Supabase client.")
    print(f"Details: {e}")
    sys.exit(1)

# The table we are interacting with
TABLE_NAME = 'keep_alive_pings'

try:
    # 1. INSERT a new row into the table to generate activity
    # The .execute() call at the end runs the query.
    print(f"Inserting a new row into '{TABLE_NAME}'...")
    insert_response = supabase.table(TABLE_NAME).insert({}).execute()

    # Check if the insert was successful
    if len(insert_response.data) > 0:
        # Get the ID of the new row we just created
        new_id = insert_response.data[0]['id']
        print(f"Successfully inserted row with ID: {new_id}")

        # 2. DELETE the exact same row immediately to keep the table clean
        print(f"Deleting the row with ID: {new_id}...")
        delete_response = supabase.table(TABLE_NAME).delete().eq('id', new_id).execute()
        
        if len(delete_response.data) > 0:
            print("Successfully deleted the row.")
        else:
            # This can happen but is usually not critical
            print("Warning: Deletion might not have been confirmed, but the operation likely succeeded.")

    else:
        print("Error: Insert operation failed. No data returned.")
        # We'll check the error details from the response
        if insert_response.error:
            print(f"API Error: {insert_response.error.message}")
        sys.exit(1)

    print("Script finished successfully. Supabase is active!")

except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)