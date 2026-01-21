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
        
        # Check for date query parameter (YYYY-MM-DD)
        date_param = request.args.get('date')
        
        if date_param:
            date_str = date_param
            log_info(f"Using requested date: {date_str}")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        # Fetch jobs for the specific date
        jobs = get_todays_jobs(date_str)
        
        log_info(f"Loaded {len(jobs)} jobs for {date_str}")
        return render_template('report.html', jobs=jobs, date=date_str)
    except Exception as e:
        log_error(f"Error loading form page: {str(e)}", exc_info=True)
        return "Error loading jobs. Please contact support.", 500

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
            source = request.form.get(f'source_{jid}', 'Other')  # Get source from hidden input
            date_val = datetime.now().strftime("%Y-%m-%d")
            
            # Server-side validation
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
                    
            except ValueError as e:
                log_error(f"Invalid revenue format for job {jid}: {e}")
                return "Invalid data: Revenue must be a number", 400
            
            # Row: [Date, Job ID, Summary, Status, Total, Net, Source, Timestamp]
            row = [date_val, jid, summary, status, total_rev, net_rev, source, timestamp]
            submission_data.append(row)
            
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
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)
