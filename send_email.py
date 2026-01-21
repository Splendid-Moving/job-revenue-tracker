import requests
from services.calendar import get_todays_jobs
from services.email_smtp import send_email_smtp
import os
from utils.logger import log_info, log_error

def main():
    try:
        log_info("Starting daily notification process")
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
        base_url = os.getenv('BASE_URL', 'http://localhost:5001/')
        if base_url.endswith('/'):
            report_url = f"{base_url}?date={today_str}"
        else:
            report_url = f"{base_url}/?date={today_str}"
        
        # Send via SMTP email
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
        
        text_body = f"Daily Job Report - {len(jobs)} Jobs\n\nPlease fill out the report: {report_url}"
        
        try:
            send_email_smtp(
                to_email=os.getenv('SMTP_EMAIL', 'info@splendidmoving.com'),
                subject=subject,
                body_html=html_body,
                body_text=text_body
            )
            log_info("Email sent successfully via SMTP")
            print("✓ Email sent successfully!")
        except Exception as e:
            log_error(f"Failed to send email via SMTP: {str(e)}", exc_info=True)
            print(f"✗ Error sending email: {e}")
            print(f"Fallback: Open this link manually:")
            print(f"\n---> {report_url} <---")
                
    except Exception as e:
        log_error(f"Fatal error in notification process: {str(e)}", exc_info=True)
        print(f"✗ Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()
