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
        
        # Require job_id param for per-job forms
        job_id_param = request.args.get('job_id')
        date_param = request.args.get('date')
        
        if not job_id_param:
            log_warning("No job_id provided")
            return "Missing job_id parameter. Use the form link from your calendar event.", 400
        
        sheets = SheetsService()
        
        log_info(f"Loading form for job_id={job_id_param}")
        
        # Fetch job data from sheets (searches all sheets for cross-month support)
        row_num, row_data, sheet_name = sheets.get_job_by_id(job_id_param)
        
        if not row_data:
            log_error(f"Job {job_id_param} not found in sheets")
            return "Job not found. This link may be expired.", 404
        
        # Check if already submitted (Status column D, index 3 is not empty)
        if len(row_data) > 3 and row_data[3]:
            log_warning(f"Job {job_id_param} already submitted")
            return render_template('already_submitted.html', date=row_data[0] if row_data else date_param)
        
        # Build job object from row data
        # Row: [Date, Job ID, Summary, Status, Total, Net, Payment, Submitted At, Source]
        job = {
            'id': row_data[1] if len(row_data) > 1 else job_id_param,
            'summary': row_data[2] if len(row_data) > 2 else 'Unknown Job',
            'source': row_data[8] if len(row_data) > 8 else 'Other',
            # Pre-fill existing values if any
            'status': row_data[3] if len(row_data) > 3 else '',
            'total_revenue': row_data[4] if len(row_data) > 4 else '',
            'net_revenue': row_data[5] if len(row_data) > 5 else '',
            'payment_type': row_data[6] if len(row_data) > 6 else '',
        }
        
        date_str = row_data[0] if row_data else date_param or datetime.now().strftime("%Y-%m-%d")
        
        log_info(f"Loading form for: {job['summary']} (sheet: {sheet_name})")
        return render_template('report.html', jobs=[job], date=date_str, single_job_mode=True)
        
    except Exception as e:
        log_error(f"Error loading form page: {str(e)}", exc_info=True)
        return f"Error loading jobs: {str(e)}", 500

@app.route('/submit', methods=['POST'])
def submit():
    try:
        log_info("Form submission received")
        
        sheets = SheetsService()
        
        # Get the single job ID from form
        job_id_list = request.form.getlist('job_id')
        
        if len(job_id_list) != 1:
            log_error(f"Expected 1 job, got {len(job_id_list)}")
            return "Invalid form submission", 400
        
        jid = job_id_list[0]
        status = request.form.get(f'status_{jid}')
        total_rev = request.form.get(f'total_{jid}', '').strip()
        net_rev = request.form.get(f'net_{jid}', '').strip()
        payment_type = request.form.get(f'payment_{jid}', '')
        
        log_info(f"Processing job {jid} with status: {status}")
        
        # Server-side validation for "Yes" status
        if status == 'Yes':
            try:
                if not total_rev:
                    log_warning(f"Missing total revenue for job {jid}")
                    total_rev = "0"
                if float(total_rev) < 0:
                    return "Invalid data: Revenue cannot be negative", 400
                
                if not net_rev:
                    log_warning(f"Missing net revenue for job {jid}")
                    net_rev = "0"
                if float(net_rev) < 0:
                    return "Invalid data: Revenue cannot be negative", 400
                
                if not payment_type:
                    return "Invalid data: Payment Type is required", 400
                    
            except ValueError:
                return "Invalid data: Revenue must be a number", 400
        else:
            # Non-Yes status: set revenues to 0
            total_rev = "0"
            net_rev = "0"
            payment_type = ""
        
        # Update the job row (auto-discovers correct sheet)
        result = sheets.update_job_row(
            job_id=jid,
            status='Completed' if status == 'Yes' else status,
            total_rev=total_rev,
            net_rev=net_rev,
            payment_type=payment_type
        )
        
        if result:
            log_info(f"Updated job {jid} in Google Sheets")
            
            # Update Calendar: Remove form link and mark as completed
            from services.calendar import mark_event_as_completed
            mark_result = mark_event_as_completed(jid)
            if mark_result:
                log_info(f"Updated calendar event {jid}")
            else:
                log_warning(f"Failed to update calendar event {jid}")
                
        else:
            log_error(f"Failed to update job {jid}")
            return "Error saving data. Please try again.", 500
        
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
from prepopulate import main as prepopulate_job

def run_prepopulate_job():
    """Wrapper to ensure scheduler job is logged properly."""
    log_info("⏰ SCHEDULED JOB TRIGGERED: prepopulate_job starting...")
    try:
        prepopulate_job()
        log_info("✅ SCHEDULED JOB COMPLETED: prepopulate_job finished successfully")
    except Exception as e:
        log_error(f"❌ SCHEDULED JOB FAILED: prepopulate_job crashed: {e}", exc_info=True)

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
            # Note: Email reminders now handled by Make.com
            # If you want to re-enable, import and call send_email here
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
        
        # Add job: Daily at 9:00 AM LA time (Pre-populate tomorrow's jobs)
        scheduler.add_job(
            run_prepopulate_job, 
            'cron', 
            hour=9, 
            minute=0, 
            timezone=la_tz,
            id='prepopulate_job',
            replace_existing=True
        )

        # Add job: Daily at 9:00 PM LA time (Reminder check)
        scheduler.add_job(
            send_reminder_job,
            'cron', 
            hour=21, 
            minute=0, 
            timezone=la_tz,
            id='reminder_job',
            replace_existing=True
        )
        
        scheduler.start()
        log_info("✅ Internal Scheduler Started: Pre-populate at 9AM, Reminder check at 9PM PST")
        
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
