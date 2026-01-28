#!/usr/bin/env python3
"""
Pre-Population Script for Per-Job Forms

Run this at 7 PM to:
1. Fetch tomorrow's jobs from Calendar
2. Create blank rows in Google Sheets
3. Add form URLs to Calendar event descriptions
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo
from services.calendar import get_tomorrows_jobs, update_event_description
from services.sheets import SheetsService
from utils.logger import log_info, log_error, log_warning


def main():
    """Main pre-population logic."""
    log_info("Starting pre-population job...")
    
    # Get base URL from environment
    base_url = os.getenv('BASE_URL', 'http://localhost:5001')
    
    # Get tomorrow's date string
    la_tz = ZoneInfo('America/Los_Angeles')
    tomorrow = datetime.now(la_tz).replace(hour=0, minute=0, second=0) 
    from datetime import timedelta
    tomorrow = tomorrow + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    
    log_info(f"Pre-populating jobs for: {tomorrow_str}")
    
    # Fetch tomorrow's jobs
    jobs = get_tomorrows_jobs()
    
    if not jobs:
        log_info("No jobs found for tomorrow. Nothing to pre-populate.")
        return
    
    log_info(f"Found {len(jobs)} jobs for tomorrow")
    
    sheets = SheetsService()
    
    for job in jobs:
        job_id = job['id']
        summary = job['summary']
        source = job.get('source', 'Other')
        
        # Check if job already exists in sheet (avoid duplicates)
        existing_row, _, _ = sheets.get_job_by_id(job_id)
        if existing_row:
            log_info(f"Job {job_id} already pre-populated. Skipping.")
            continue
        
        # Create blank row in Sheets
        sheets.create_job_row(
            date_str=tomorrow_str,
            job_id=job_id,
            summary=summary,
            source=source
        )
        
        # Generate form URL
        form_url = f"{base_url}/?job_id={job_id}&date={tomorrow_str}"
        
        # Update calendar event with form URL
        update_event_description(job_id, form_url)
        
        log_info(f"Pre-populated job: {summary}")
    
    log_info(f"Pre-population complete. {len(jobs)} jobs processed.")


if __name__ == "__main__":
    main()
