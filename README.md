# Splendid Moving - Job Revenue Tracker

Automated daily job revenue reporting system that fetches moving jobs from Google Calendar and creates a web form to collect revenue data, which is then stored in Google Sheets.

---

## 📋 Overview

This system automates the daily workflow of tracking revenue for moving jobs:

1. **Fetches** today's jobs from Google Calendar (`info@splendidmoving.com`)
2. **Generates** a web form with 3 questions per job
3. **Sends** an email notification with the form link
4. **Saves** submitted data to Google Sheets (auto-creates monthly tabs like "Jan 2026")

---

## 🏗️ Architecture

```
┌─────────────────┐
│ Google Calendar │ ──> Fetch jobs for today
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Flask App     │ ──> Generate HTML form
│ (localhost:5001)│
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Email (SMTP)   │ ──> Send form link
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ User fills form │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Google Sheets   │ ──> Store revenue data
└─────────────────┘
```

---

## 🔑 Credentials Required

### 1. Service Account (Google Cloud)
- **File**: `service_account.json`
- **Email**: `moving-tracker-server@ad-report-automation-484101.iam.gserviceaccount.com`
- **Permissions**: Must have access to:
  - Google Calendar (`info@splendidmoving.com`)
  - Google Sheets (Job Revenue Tracker)

### 2. SMTP Email (Gmail App Password)
- **File**: `.env`
- **Required variables**:
  ```
  SMTP_EMAIL=info@splendidmoving.com
  SMTP_PASSWORD=your_16_char_app_password
  USE_SMTP=true
  ```
- **How to get App Password**: https://myaccount.google.com/apppasswords

---

## 📊 Data Flow

### Questions Asked Per Job:
1. **Did the move happen?** (Yes / Cancelled / Rescheduled / Other)
2. **Total revenue collected?** ($)
3. **Net revenue collected?** ($)

### Google Sheet Columns:
| Date | Job ID | Summary | Status | Total Revenue | Net Revenue | Source | Submitted At |
|------|--------|---------|--------|---------------|-------------|--------|--------------|

**Source Detection** (based on Google Calendar event colors):
- 🟠 Orange (`#ffb878`) = **Yelp**
- 🟢 Teal (`#7ae7bf`) = **Google LSA**
- ⚪ No color = **Other**

> **Note**: Colors must be set on the event itself in Google Calendar (not just visual calendar color)

---

## 🚀 Daily Usage

### Step 1: Start the Form Server
```bash
cd /Users/nikti/Desktop/Projects/splendid_moving/job_form_automation
python3 app.py
```
- Server runs on: http://localhost:5001/
- Keep this terminal window open

### Step 2: Send Daily Notification
```bash
# In a new terminal window
python3 send_email.py
```
- Fetches today's jobs
- Sends email to `info@splendidmoving.com`
- Email contains link to form

### Step 3: Fill Out Form
- Click link in email
- Form shows all jobs for today
- Submit revenue data
- Data automatically saves to Google Sheets

---

## 📁 Project Structure

```
job_form_automation/
├── app.py                  # Flask web server (form display & submission)
├── send_email.py           # Email notification script
├── config.py               # Configuration (calendar ID, sheet ID, color mapping)
├── .env                    # SMTP credentials (DO NOT COMMIT)
├── service_account.json    # Google Service Account key (DO NOT COMMIT)
│
├── services/
│   ├── auth.py            # Google API authentication
│   ├── calendar.py        # Fetch jobs from Google Calendar
│   ├── sheets.py          # Write data to Google Sheets
│   └── email_smtp.py      # Send emails via Gmail SMTP
│
├── templates/
│   ├── report.html        # Main form template
│   └── success.html       # Success page after submission
│
└── requirements.txt       # Python dependencies
```

---

## ⚙️ Configuration

### `config.py`

**Calendar Settings:**
```python
CALENDAR_ID = 'info@splendidmoving.com'
```

**Google Sheet:**
```python
TARGET_SPREADSHEET_ID = "1USAoTNsUKIzg4XKzyeQANUYDNQCblQa8ROJ2Q3d1s7k"
```

**Color-to-Source Mapping:**
```python
COLOR_SOURCE_MAP = {
    '6': 'Yelp',        # Orange
    '2': 'Google LSA',  # Teal
}
```

**Email:**
```python
TARGET_EMAIL = 'info@splendidmoving.com'
```

---

## 🔧 Troubleshooting

### "localhost refused to connect"
- **Cause**: Flask app not running
- **Fix**: Run `python3 app.py`

### "Duplicate rows in Google Sheets"
- **Cause**: Flask debug mode spawning multiple processes
- **Fix**: Already fixed with `use_reloader=False` in `app.py`

### "Colors not detected"
- **Cause**: Event colors not set via API (only visual in UI)
- **Fix**: 
  1. Open event in Google Calendar
  2. Click Edit → Select color from dropdown
  3. Save

### "Email not sending"
- **Cause**: Invalid SMTP credentials
- **Fix**: Check `.env` file has correct app password

### "No jobs found"
- **Cause**: Service Account doesn't have calendar access
- **Fix**: Share calendar with `moving-tracker-server@ad-report-automation-484101.iam.gserviceaccount.com`

---

## 🏗 System Architecture

This project uses a **Hybrid Architecture** for maximum reliability and zero maintenance.

### 1. The Web App (Railway)
*   **Status**: 🟢 Online 24/7
*   **URL**: `https://web-production-755dc.up.railway.app`
*   **Purpose**: Hosts the actual form you fill out.
*   **Why Railway?**: It gives us a permanent, secure URL accessible from any device (phone or laptop), so you don't need your computer running to submit data.

### 2. The Automation (GitHub Actions)
*   **Status**: 🟢 Runs Daily @ 6 PM (LA Time)
*   **Purpose**: The "Alarm Clock" that wakes up, checks Google Calendar for jobs, and emails you the link.
*   **Why GitHub Actions?**: 
    1. **Reliability**: It runs on GitHub's servers, so it works even if your computer is off or sleeping.
    2. **Cost**: It is completely free for this usage.
    3. **Separation**: It keeps the "trigger" separate from the "website", ensuring the email sends even if the website were momentarily restarting.

---

## 🔄 How It Works Daily

1. **6:00 PM**: GitHub Actions starts up.
2. It fetches jobs from **Google Calendar** (using "Los Angeles" timezone).
3. It sends an email to `info@splendidmoving.com` with the **Railway Link**.
4. You click the link, fill out the revenue, and click **Submit**.
5. Data is securely saved to **Google Sheets**.

---

---

## 📦 Dependencies

Install with:
```bash
pip install -r requirements.txt
```

**Required packages:**
- `flask` - Web framework
- `google-api-python-client` - Google APIs
- `google-auth-httplib2` - Authentication
- `google-auth-oauthlib` - OAuth support
- `python-dotenv` - Environment variables
- `requests` - HTTP requests

---

## 🔐 Security Notes

**DO NOT commit these files to Git:**
- `.env` (contains SMTP password)
- `service_account.json` (contains private key)

Add to `.gitignore`:
```
.env
service_account.json
*.pyc
__pycache__/
```

---

## 📝 Sheet Behavior

- **Auto-creates monthly tabs**: "Jan 2026", "Feb 2026", etc.
- **Header row added automatically** on first use of each month
- **Appends data** to the bottom of the current month's tab
- **Old tabs preserved** for historical data

---

## 🎨 Customization

### Change Form Styling
Edit `templates/report.html` - CSS is inline in the `<style>` tag

### Add More Questions
1. Update `templates/report.html` (add form fields)
2. Update `app.py` (capture new fields in `/submit` route)
3. Update `services/sheets.py` (add columns to header)

### Change Email Template
Edit `send_email.py` - modify `html_body` variable

---

## 📞 Support

**Service Account Email**: `moving-tracker-server@ad-report-automation-484101.iam.gserviceaccount.com`  
**Google Sheet**: [Job Revenue Tracker](https://docs.google.com/spreadsheets/d/1USAoTNsUKIzg4XKzyeQANUYDNQCblQa8ROJ2Q3d1s7k)  
**Calendar**: `info@splendidmoving.com`

---

## ✅ Quick Start Checklist

- [ ] Service Account has calendar access
- [ ] Service Account has sheet access
- [ ] `.env` file created with SMTP credentials
- [ ] `python3 app.py` running
- [ ] Test email sent successfully
- [ ] Form accessible at http://localhost:5001/
- [ ] Test submission saved to Google Sheets

---

**Last Updated**: January 20, 2026
