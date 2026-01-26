from flask import Flask, render_template, request, redirect, url_for
from services.calendar import get_todays_jobs
from services.sheets import SheetsService
from datetime import datetime
from utils.logger import log_info, log_error, log_warning
import os

app = Flask(__name__)

@app.route('/')
def index():
    try:
        log_info("Form page accessed")
        # Trigger deployment 2026-01-26 11:35
        
        # Check for date query parameter (YYYY-MM-DD)
        date_param = request.args.get('date')
        
        if date_param:
            date_str = date_param
            log_info(f"Using requested date: {date_str}")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        log_info(f"Checking for existing submission for {date_str}")
        
        # Check against Google Sheets to prevent duplicates (unless force=true)
        sheets = SheetsService()
        if not request.args.get('force') and sheets.check_date_exists(date_str):
            log_warning(f"Duplicate submission attempted for {date_str}")
            return render_template('already_submitted.html', date=date_str)

        # Fetch jobs for the specific date
        jobs = get_todays_jobs(date_str)
        
        log_info(f"Loaded {len(jobs)} jobs for {date_str}")
        return render_template('report.html', jobs=jobs, date=date_str)
    except Exception as e:
        log_error(f"Error loading form page: {str(e)}", exc_info=True)
        # Expose error for debugging
        return f"Error loading jobs: {str(e)}", 500

@app.route('/submit', methods=['POST'])
def submit():
    try:
        log_info("Form submission received")
        # Process form data
        # Form structure: we iterating over jobs. 
        # Inputs will likely be named like "status_<job_id>", "revenue_<job_id>", etc.
        
        # We need to reconstruct which jobs were submitted. 
        # Or strict hidden input "job_ids" list?
        
        # Let's iterate over keys to find job IDs
        
        submission_data = [] # List of rows to append
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # We can't easily know ALL job IDs just from request.form unless we pass them.
        # But we can assume inputs are strictly named.
        
        # Let's group by prefix
        # job_{id}_status
        # job_{id}_total
        # job_{id}_net
        # job_{id}_summary (hidden)
        
        # Grouping
        job_ids = set()
        for key in request.form:
            if key.startswith("job_") and "_status" in key:
                # Extract ID: job_xyz123_status -> xyz123
                # But IDs might have underscores. 
                # Better: use a hidden input "job_ids" that is a comma separated list.
                pass

        # Better approach: request.form.getlist('job_id')
        job_id_list = request.form.getlist('job_id')
        log_info(f"Processing {len(job_id_list)} job submissions")
        
        for jid in job_id_list:
            summary = request.form.get(f'summary_{jid}')
            status = request.form.get(f'status_{jid}')
            total_rev = request.form.get(f'total_{jid}', '').strip()
            net_rev = request.form.get(f'net_{jid}', '').strip()
            # Get source (from hidden input) and Payment Type
            source = request.form.get(f'source_{jid}', 'Other')
            payment_type = request.form.get(f'payment_{jid}', '') 

            # Fix: Use the date passed from the form (date_reported_for) 
            # instead of datetime.now() to ensure duplicate check (check_date_exists) works correctly.
            date_val = request.form.get('date_reported_for')
            if not date_val:
                log_warning("Missing date_reported_for, falling back to today")
                date_val = datetime.now().strftime("%Y-%m-%d")

            # Server-side logic for conditional fields
            if status == 'Yes':
                # Determine "Yes" means we validate and save
                try:
                    # Validate total revenue
                    if not total_rev:
                        log_warning(f"Missing total revenue for job {jid}")
                        total_rev = "0"
                    total_rev_float = float(total_rev)
                    if total_rev_float < 0:
                        log_error(f"Negative total revenue for job {jid}: {total_rev}")
                        return "Invalid data: Revenue cannot be negative", 400
                    
                    # Validate net revenue
                    if not net_rev:
                        log_warning(f"Missing net revenue for job {jid}")
                        net_rev = "0"
                    net_rev_float = float(net_rev)
                    if net_rev_float < 0:
                        log_error(f"Negative net revenue for job {jid}: {net_rev}")
                        return "Invalid data: Revenue cannot be negative", 400
                    
                    # Validate Payment Type
                    if not payment_type:
                         log_warning(f"Missing payment type for job {jid}")
                         return "Invalid data: Payment Type is required", 400

                except ValueError as e:
                    log_error(f"Invalid revenue format for job {jid}: {e}")
                    return "Invalid data: Revenue must be a number", 400

                # Row: [Date, Job ID, Summary, Status, Total, Net, Payment, Submitted At, Source]
                row = [date_val, jid, summary, status, total_rev, net_rev, payment_type, timestamp, source]
                submission_data.append(row)
            
            else:
                # Status is Cancelled/Rescheduled/Other
                # We do NOT save to sheets (as requested) or we save with 0?
                # User request: "only add the jobs to the google sheets, if it was marked yes."
                log_info(f"Skipping job {jid} (Status: {status})")
                pass
            
        # Write to Sheets
        if submission_data:
            sheets = SheetsService()
            result = sheets.append_job_data(submission_data)
            if result:
                log_info(f"Successfully saved {len(submission_data)} jobs to Google Sheets")
            else:
                log_error("Failed to save data to Google Sheets")
                return "Error saving data. Please try again.", 500
        else:
            log_warning("No submission data received")
            
        return render_template('success.html')
        
    except Exception as e:
        log_error(f"Error processing form submission: {str(e)}", exc_info=True)
        return "Error submitting form. Please try again.", 500


if __name__ == '__main__':
    # Railway sets PORT environment variable
    port = int(os.getenv('PORT', 5001))
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Start the scheduler locally
    # Note: In production (Gunicorn), the scheduler is started by the code above `if __name__`
    # But we need to ensure it runs. 
    # Actually, putting it in global scope (outside if main) ensures it runs in Gunicorn too.
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)

# Scheduler Setup (Global Scope to run in Gunicorn)
from apscheduler.schedulers.background import BackgroundScheduler
from zoneinfo import ZoneInfo
from send_email import main as send_email_job

def send_reminder_job():
    """
    Check if a submission exists for today at 9:00 PM. 
    If not, send a reminder email.
    """
    try:
        from zoneinfo import ZoneInfo
        la_tz = ZoneInfo('America/Los_Angeles')
        today_str = datetime.now(la_tz).strftime("%Y-%m-%d")
        
        sheets = SheetsService()
        if not sheets.check_date_exists(today_str):
            log_info(f"Report for {today_str} missing at 9:00 PM. Sending reminder.")
            send_email_job(is_reminder=True)
        else:
            log_info(f"Report for {today_str} already submitted. Skipping reminder.")
    except Exception as e:
        log_error(f"Error in send_reminder_job: {e}")

def start_scheduler():
    try:
        # Check if scheduler is already running or if we are in a reloader child process to avoid double run
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            return

        scheduler = BackgroundScheduler()
        
        # Determine strict timezone
        la_tz = ZoneInfo('America/Los_Angeles')
        
        # Add job: Daily at 6:00 PM LA time
        scheduler.add_job(
            send_email_job, 
            'cron', 
            hour=18, 
            minute=0, 
            timezone=la_tz,
            id='daily_email_job',
            replace_existing=True
        )

        # Add job: Daily at 9:00 PM LA time (Reminder)
        scheduler.add_job(
            send_reminder_job,
            'cron', 
            hour=21, 
            minute=0, 
            timezone=la_tz,
            id='reminder_email_job',
            replace_existing=True
        )
        
        scheduler.start()
        log_info("✅ Internal Scheduler Started: Daily at 6PM and Reminder at 9PM PST")
        
        # Print next run time for verification
        jobs = scheduler.get_jobs()
        if jobs:
            print(f"Next scheduled run: {jobs[0].next_run_time}")
            
    except Exception as e:
        log_error(f"Failed to start scheduler: {e}")

# Start the scheduler immediately on import
# We use a primitive check to ensure we are not in a build step or similar
if os.environ.get('RAILWAY_STATIC_URL') or os.environ.get('RAILWAY_ENVIRONMENT'):
   # We are likely in production
   start_scheduler()
else:
   # Local development - start it too
   start_scheduler()
