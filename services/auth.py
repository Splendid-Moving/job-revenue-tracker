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
            
            # Aggressive Repair: Handle one-line, escaped, or truncated keys
            if 'private_key' in service_account_info:
                pk = service_account_info['private_key']
                
                # 1. Strip headers, footers, and whitespace
                clean_key = pk.replace('-----BEGIN PRIVATE KEY-----', '')
                clean_key = clean_key.replace('-----END PRIVATE KEY-----', '')
                clean_key = clean_key.replace('\\n', '').replace('\n', '').strip()
                
                # 2. Re-wrap with proper PEM formatting
                # Google expects the header, the key, and the footer with newlines
                formatted_key = f"-----BEGIN PRIVATE KEY-----\n{clean_key}\n-----END PRIVATE KEY-----\n"
                service_account_info['private_key'] = formatted_key
            
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
