#!/usr/bin/env python3
"""
Pre-Population & Reconciliation Script

Run daily at 9 AM to:
1. Fetch tomorrow's jobs from Calendar → create rows + form URLs
2. Reconcile yesterday's jobs → backfill any that were missed
"""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from services.calendar import get_tomorrows_jobs, get_yesterdays_jobs, update_event_description
from services.sheets import SheetsService
from utils.logger import log_info, log_error, log_warning


def process_jobs(jobs, date_str, base_url, sheets, label=""):
    """
    Process a list of calendar jobs:
    - Skip if already in Google Sheets (duplicate check)
    - Create a blank row in the correct monthly sheet
    - Add a form URL to the calendar event description

    Returns the number of newly added jobs.
    """
    added = 0

    for job in jobs:
        job_id = job['id']
        summary = job['summary']
        source = job.get('source', 'Other')

        # Check if job already exists in sheet (avoid duplicates)
        existing_row, _, _ = sheets.get_job_by_id(job_id)
        if existing_row:
            log_info(f"[{label}] Job {job_id} already in sheet. Skipping.")
            continue

        # Create blank row in Sheets
        sheets.create_job_row(
            date_str=date_str,
            job_id=job_id,
            summary=summary,
            source=source
        )

        # Generate form URL
        form_url = f"{base_url}/?job_id={job_id}&date={date_str}"

        # Update calendar event with form URL
        update_event_description(job_id, form_url)

        log_info(f"[{label}] Pre-populated job: {summary}")
        added += 1

    return added


def main():
    """Main pre-population + reconciliation logic."""
    log_info("Starting pre-population job...")

    base_url = os.getenv('BASE_URL', 'http://localhost:5001')
    la_tz = ZoneInfo('America/Los_Angeles')
    sheets = SheetsService()

    # ── 1. Pre-populate tomorrow's jobs ──────────────────────────
    tomorrow = datetime.now(la_tz) + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    log_info(f"Pre-populating jobs for tomorrow: {tomorrow_str}")
    tomorrow_jobs = get_tomorrows_jobs()

    if tomorrow_jobs:
        log_info(f"Found {len(tomorrow_jobs)} jobs for tomorrow")
        added = process_jobs(tomorrow_jobs, tomorrow_str, base_url, sheets, label="tomorrow")
        log_info(f"Tomorrow: {added} new jobs added, {len(tomorrow_jobs) - added} already existed")
    else:
        log_info("No jobs found for tomorrow.")

    # ── 2. Reconcile yesterday's jobs ────────────────────────────
    yesterday = datetime.now(la_tz) - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")

    log_info(f"Reconciling yesterday's jobs for: {yesterday_str}")
    yesterday_jobs = get_yesterdays_jobs()

    if yesterday_jobs:
        log_info(f"Found {len(yesterday_jobs)} jobs for yesterday in calendar")
        added = process_jobs(yesterday_jobs, yesterday_str, base_url, sheets, label="yesterday")
        if added > 0:
            log_info(f"Yesterday reconciliation: {added} missing jobs backfilled")
        else:
            log_info("Yesterday reconciliation: all jobs already in sheet ✓")
    else:
        log_info("No jobs found for yesterday in calendar.")

    log_info("Pre-population + reconciliation complete.")


if __name__ == "__main__":
    main()
