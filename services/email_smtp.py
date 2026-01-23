import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def send_email_smtp(to_email, subject, body_html, body_text=None):
    """
    Send email using Gmail SMTP with App Password.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text fallback (optional)
    """
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_email or not smtp_password:
        raise ValueError("SMTP credentials not found. Please set SMTP_EMAIL and SMTP_PASSWORD in .env file")
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['From'] = smtp_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Add plain text version if provided
    if body_text:
        msg.attach(MIMEText(body_text, 'plain'))
    
    # Add HTML version
    msg.attach(MIMEText(body_html, 'html'))
    
    # Connect to Gmail SMTP server
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(smtp_email, smtp_password)
        server.send_message(msg)
        print(f"✓ Email sent successfully to {to_email}")
        return True
