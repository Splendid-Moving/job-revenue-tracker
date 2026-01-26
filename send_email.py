import requests
from services.calendar import get_todays_jobs
import os
from utils.logger import log_info, log_error

def main(is_reminder=False):
    try:
        log_info("Starting daily notification process" + (" (REMINDER)" if is_reminder else ""))
        print("Checking for jobs...")
        jobs = get_todays_jobs()
        
        if not jobs:
            log_info("No jobs found for today")
            print("No jobs today. Skipping notification.")
            return

        log_info(f"Found {len(jobs)} jobs for today")
        print(f"Found {len(jobs)} jobs.")
        
        # Get today's date string for the URL
        from datetime import datetime
        from zoneinfo import ZoneInfo
        la_tz = ZoneInfo('America/Los_Angeles')
        today_str = datetime.now(la_tz).strftime("%Y-%m-%d")
        
        # URL to the Flask app (from environment variable or localhost)
        base_url = os.getenv('BASE_URL', 'https://web-production-755dc.up.railway.app')
        # Send via Make.com Webhook
        if is_reminder:
            subject = f"⚠️ REMINDER: Missing Daily Job Report - {len(jobs)} Jobs"
        else:
            subject = f"ACTION REQUIRED: Daily Job Report - {len(jobs)} Jobs"
        
        # Create HTML email body
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Daily Moving Jobs Report</h2>
                <p>You have <strong>{len(jobs)} jobs</strong> scheduled for today.</p>
                <p>Please fill out the revenue report:</p>
                <p style="margin: 20px 0;">
                    <a href="{report_url}" 
                       style="background: #27ae60; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        Open Report Form
                    </a>
                </p>
                <p style="color: #666; font-size: 12px;">
                    Link: <a href="{report_url}">{report_url}</a>
                </p>
            </body>
        </html>
        """
        
        webhook_url = "https://hook.us2.make.com/1i4fchxr99y4cu4ryghgfcnhhvz86c3b"
        
        import time
        max_retries = 3
        retry_delay = 5  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                log_info(f"Sending email metadata to Make.com (Attempt {attempt}/{max_retries})...")
                
                payload = {
                    "subject": subject,
                    "body": html_body,
                    "to_email": os.getenv('SMTP_EMAIL', 'info@splendidmoving.com') # Pass recipient just in case webhook needs it
                }
                
                response = requests.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                
                log_info("Email trigger sent successfully to Make.com")
                print("✓ Email trigger sent successfully!")
                break # Success, exit loop
            except Exception as e:
                log_error(f"Attempt {attempt} failed: {str(e)}")
                if attempt < max_retries:
                    log_info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    log_error(f"All {max_retries} attempts failed.", exc_info=True)
                    print(f"✗ Error sending webhook after {max_retries} attempts: {e}")
                    raise # Re-raise to alert scheduler
                
    except Exception as e:
        log_error(f"Fatal error in notification process: {str(e)}", exc_info=True)
        print(f"✗ Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()
