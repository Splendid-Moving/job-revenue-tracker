# GitHub Actions Setup for Daily Automation

## What This Does
Automatically sends the daily job report email at **6 PM Los Angeles time** every day.

## Setup Instructions

### 1. Add Secrets to GitHub Repository

Go to: https://github.com/Splendid-Moving/job-revenue-tracker/settings/secrets/actions

Click **"New repository secret"** and add these 4 secrets:

#### `SERVICE_ACCOUNT_JSON`
Copy the entire content of your `service_account.json` file as a single line (no line breaks).

You can generate it with:
```bash
cat service_account.json | tr -d '\n'
```

#### `SMTP_EMAIL`
```
info@splendidmoving.com
```

#### `SMTP_PASSWORD`
Your Gmail App Password (16 characters from https://myaccount.google.com/apppasswords)

#### `BASE_URL`
```
https://your-railway-app.railway.app
```

### 2. Push the Workflow to GitHub

The workflow file is already created at `.github/workflows/daily-email.yml`

Just commit and push:
```bash
git add .github/workflows/daily-email.yml
git commit -m "Add daily automation at 6 PM LA time"
git push
```

### 3. Test It

Go to: https://github.com/Splendid-Moving/job-revenue-tracker/actions

Click on "Daily Job Report Email" → "Run workflow" to test manually

### 4. Monitor

The workflow will run automatically every day at 6 PM Los Angeles time.

Check the Actions tab to see logs and confirm it's working.

---

## How It Works

- **Schedule**: `0 2 * * *` (2 AM UTC = 6 PM PST)
- **Runs on**: GitHub's free servers (no cost)
- **Sends**: Email notification with form link
- **Logs**: Available in GitHub Actions tab

## Timezone Note

GitHub Actions uses UTC time. The cron is set to 2 AM UTC which equals:
- 6 PM PST (Pacific Standard Time)
- 7 PM PDT (Pacific Daylight Time)

If you need exactly 6 PM year-round, you'd need to adjust the cron twice a year for DST changes.
