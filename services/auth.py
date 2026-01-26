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
            # Load from environment variable (Railway)
            data = raw_env
            
            # 1. Handle double-stringification (If Railway sends it as a string-wrapped string)
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    pass
            
            # 2. Handle Nesting (If user pasted the whole Railway JSON payload)
            if isinstance(data, dict) and 'SERVICE_ACCOUNT_JSON' in data:
                data = data['SERVICE_ACCOUNT_JSON']
                # Try parsing again if the inner value is still stringified
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except:
                        pass
            
            # data should now be our service_account_info dict
            service_account_info = data
            
            # Aggressive Repair: Handle one-line, escaped, or truncated keys
            if isinstance(service_account_info, dict) and 'private_key' in service_account_info:
                pk = service_account_info['private_key']
                
                # 1. Strip ALL junk - headers, footers, newlines, escaped newlines, quotes, and spaces
                # This leaves us with just the naked Base64 string
                junk_to_remove = [
                    '-----BEGIN PRIVATE KEY-----', 
                    '-----END PRIVATE KEY-----',
                    '\\n', '\n', '\r', ' ', '\t', '"', "'"
                ]
                clean_key = pk
                for junk in junk_to_remove:
                    clean_key = clean_key.replace(junk, '')
                
                clean_key = clean_key.strip()
                
                # 2. PEM format requires 64-character line wrapping
                # Build the perfect PEM structure from the naked key
                lines = [clean_key[i:i+64] for i in range(0, len(clean_key), 64)]
                formatted_key = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(lines) + "\n-----END PRIVATE KEY-----\n"
                
                service_account_info['private_key'] = formatted_key
                print(f"DEBUG: Final Key Cleaned (Length: {len(clean_key)})")
            
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
