# Railway Deployment Instructions

## Environment Variables to Set in Railway

Copy the content of `service_account.json` and set these environment variables:

```bash
SERVICE_ACCOUNT_JSON=<paste entire JSON content here as one line>
SMTP_EMAIL=info@splendidmoving.com
SMTP_PASSWORD=qplc imat wvbn rtrd
BASE_URL=https://your-app-name.railway.app
```

## Steps to Deploy

1. **Push to GitHub** (authentication required)
2. **Connect Railway to GitHub repo**
3. **Set environment variables** in Railway dashboard
4. **Deploy automatically**

## GitHub Authentication

Run one of these commands:

```bash
# Option 1: GitHub CLI
gh auth login

# Option 2: Personal Access Token
git push https://YOUR_TOKEN@github.com/Splendid-Moving/job-revenue-tracker.git main
```

## After Deployment

Test the app at your Railway URL and update `BASE_URL` environment variable.
