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
        if os.getenv('SERVICE_ACCOUNT_JSON'):
            # Load from environment variable (Railway)
            service_account_info = json.loads(os.getenv('SERVICE_ACCOUNT_JSON'))
            
            # Fix: Handle newline characters in private key that might be escaped
            if 'private_key' in service_account_info:
                service_account_info['private_key'] = service_account_info['private_key'].replace('\\n', '\n')
            
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
