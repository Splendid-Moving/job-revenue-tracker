import sys
from services.calendar import get_todays_jobs
from services.forms import create_daily_form
from services.email import send_email

def main():
    print("Step 1: Fetching today's jobs...")
    jobs = get_todays_jobs()
    
    if not jobs:
        print("No jobs found for today. Exiting.")
        return

    print(f"Found {len(jobs)} jobs.")
    
    print("Step 2: Creating Google Form...")
    form_result = create_daily_form(jobs)
    
    if not form_result:
        print("Failed to create form.")
        return
        
    form_url = form_result['responderUri']
    print(f"Form ready at: {form_url}")
    
    print("Step 3: Sending Email...")
    subject = f"Daily Moving Jobs Form - {len(jobs)} Jobs"
    body = f"Hello,\n\nPlease fill out the daily report for the following jobs:\n\nForm Link: {form_url}\n\nThanks,\nAutomation Bot"
    
    send_email(subject, body)
    
    print("Done!")

if __name__ == '__main__':
    main()
