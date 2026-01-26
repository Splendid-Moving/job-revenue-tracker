from google.oauth2 import service_account
from googleapiclient.discovery import build
import config
import os
import json

def get_creds():
    """
    Load Google Service Account credentials.
    Supports both local file and Railway environment variable.
    """
    try:
        # Check if running on Railway (env var set)
        raw_env = os.getenv('SERVICE_ACCOUNT_JSON')
        if raw_env:
            import base64
            
            # Decode from Base64 first (solves ALL escaping/newline issues)
            try:
                decoded_bytes = base64.b64decode(raw_env)
                decoded_str = decoded_bytes.decode('utf-8')
                service_account_info = json.loads(decoded_str)
                print("DEBUG: Successfully decoded Base64 credentials")
            except Exception as decode_error:
                # Fallback: try parsing as raw JSON (for backwards compatibility)
                print(f"DEBUG: Base64 decode failed ({decode_error}), trying raw JSON...")
                service_account_info = json.loads(raw_env)
            
            creds = service_account.Credentials.from_service_account_info(
                service_account_info, scopes=config.SCOPES)
        else:
            # Load from file (local development)
            creds = service_account.Credentials.from_service_account_file(
                config.SERVICE_ACCOUNT_FILE, scopes=config.SCOPES)
        return creds
    except Exception as e:
        print(f"Error loading credentials: {e}")
        raise

def get_service(api_name, api_version, creds=None):
    """
    Returns an authenticated service object.
    """
    if not creds:
        creds = get_creds()
    
    if not creds:
        raise Exception("Could not authenticate. Check service_account.json.")

    return build(api_name, api_version, credentials=creds)
