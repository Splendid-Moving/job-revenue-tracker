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
                
                # Debug: Show hex of first 50 chars to see what the "hidden" newlines are
                try:
                    hex_sample = pk[:50].encode('utf-8').hex(' ')
                    print(f"DEBUG: Key Hex Sample: {hex_sample}")
                except:
                    pass
                
                # 1. Strip headers, footers, and ALL whitespace/escape sequences
                # We want just the raw Base64 data
                clean_key = pk.replace('-----BEGIN PRIVATE KEY-----', '')
                clean_key = clean_key.replace('-----END PRIVATE KEY-----', '')
                
                # Remove every possible representation of a newline/space
                for junk in ['\\n', '\n', '\r', ' ', '\t']:
                    clean_key = clean_key.replace(junk, '')
                
                clean_key = clean_key.strip()
                
                # 2. PEM format requires 64-character line wrapping
                # This is a strict requirement for the 'cryptography' library
                lines = [clean_key[i:i+64] for i in range(0, len(clean_key), 64)]
                formatted_key = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(lines) + "\n-----END PRIVATE KEY-----\n"
                
                service_account_info['private_key'] = formatted_key
                print(f"DEBUG: Repaired Key Length: {len(formatted_key)}")
                print(f"DEBUG: Repaired Key Tail: ...{formatted_key[-30:].strip()}")
            
            creds = service_account.Credentials.from_service_account_info(
                service_account_info, scopes=config.SCOPES)
        else:
            # Load from file (local development)
            creds = service_account.Credentials.from_service_account_file(
                config.SERVICE_ACCOUNT_FILE, scopes=config.SCOPES)
        return creds
    except Exception as e:
        # Don't log the full key in the error, just the message
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
