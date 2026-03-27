import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Create the Client
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

print("--- Checking Available Models ---")
try:
    # In the new SDK, the access is via client.models.list()
    for m in client.models.list():
        # Clean print of the name that can be used in the .env
        # We remove the 'models/' prefix because the Client automatically adds it in calls
        model_id = m.name.replace("models/", "")
        print(f"Available Model ID: {model_id}")
except Exception as e:
    print(f"Error: {e}")