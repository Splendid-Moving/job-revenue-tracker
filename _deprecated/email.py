import base64
from email.message import EmailMessage
import config
from services.auth import get_service

def send_email(subject, body, to_email=None):
    """
    Sends an email using the Gmail API.
    """
    if not to_email:
        to_email = config.TARGET_EMAIL
        
    service = get_service('gmail', 'v1')
    
    message = EmailMessage()
    message.set_content(body)
    message['To'] = to_email
    message['Subject'] = subject
    
    # Encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    create_message = {
        'raw': encoded_message
    }
    
    try:
        sent_message = service.users().messages().send(userId="me", body=create_message).execute()
        print(f"Email sent to {to_email}. Message Id: {sent_message['id']}")
        return sent_message
    except Exception as e:
        print(f"An error occurred sending email: {e}")
        return None
