# Splendid Moving - Job Revenue Tracker

Automated job revenue reporting system that pre-populates tomorrow's moving jobs from Google Calendar into Google Sheets and manages per-event reporting links.

---

## 📋 Overview

The system automates the tracking of revenue by pre-preparing the reporting infrastructure every day:

1.  **Pre-Populates**: Every day at **9:00 AM**, the system fetches tomorrow's jobs from Google Calendar.
2.  **Initializes Sheets**: Creates a blank row for each job in the monthly Google Sheet (e.g., "Feb 2026").
3.  **Links Calendar**: Adds a unique reporting URL directly to the description of each Google Calendar event.
4.  **Collects Data**: Moving crews click the link in their calendar, fill out the Russian-localized form, and submit.
5.  **Finalizes**: Upon submission, the row in Sheets is updated with revenue data, and the Calendar event is marked as **"✅ Form Completed"**.

---

## 🏗️ Architecture

```
┌─────────────────┐
│ Google Calendar │ <───┐ 1. Fetch Tomorrow's Jobs (9 AM)
└─────────────────┘     │ 3. Add Form Link to Description
         │              │ 5. Mark "Completed" on Submit
         ▼              │
┌─────────────────┐     │
│   Railway App   │ ────┘
│ (Internal Cron) │ ────┐
└─────────────────┘     │
         │              │ 2. Create blank rows (9 AM)
         ▼              │ 4. Update with Revenue on Submit
┌─────────────────┐     │
│  Google Sheets  │ <────┘
└─────────────────┘
```

---

## 🔑 Key Features

### 1. Per-Job Reporting
Instead of one large form, each job has its own unique Link. This prevents data conflicts and ensures every single move is accounted for.

### 2. Global Summary Dashboard
The **"Summary"** tab in Google Sheets provides:
- **Chronological History**: Monthly revenue totals for your entire business history.
- **Source Breakdown**: Separate columns for **Yelp** and **Google LSA** revenue.
- **Grand Totals**: Lifetime revenue tracking at the bottom.

### 3. Russian Localization
The form is fully translated to Russian for the crew's convenience:
- `Состоялся ли мув?` (Did the move happen?)
- `Тотал (вместе с депозитом)` (Total Revenue)
- `Остаток` (Net Revenue)

### 4. Smart Scheduling
- **9:00 AM**: Pre-population run (prepares tomorrow's jobs).
- **9:00 PM**: Reminder check (detects if any reports for *today* are still missing).

---

## ⚙️ Configuration

### Source Detection
The system automatically identifies the lead source:
1.  **Description**: Looks for "Source: Yelp" or "Source: Google LSA" in the notes.
2.  **Fallback (Color)**:
    - � Orange (`#ffb878`) = **Yelp**
    - 🟢 Teal (`#7ae7bf`) = **Google LSA**
    - ⚪ Other = **Other**

### Calendar Filtering
To prevent personal tasks from appearing in the sheet, the system only processes events that contain **"customer phone"** and **"date"** in their description field.

---

## 📁 Project Structure

```
job_form_automation/
├── app.py                  # Flask server + Internal Scheduler
├── prepopulate.py         # Logic for fetching jobs & creating rows
├── config.py               # Sheet IDs, Calendar IDs, and color maps
├── services/
│   ├── calendar.py        # Google Calendar API integration
│   ├── sheets.py          # Google Sheets API (Dashboard & Data)
│   └── auth.py            # API Authentication
└── templates/
    ├── report.html        # Russian-localized reporting form
    └── success.html       # Success confirmation
```

---

## 🚀 Deployment

The app is hosted on **Railway** and connects to the **Splendid Moving** Google Service Account.

**Google Sheet**: [Job Revenue Tracker](https://docs.google.com/spreadsheets/d/1USAoTNsUKIzg4XKzyeQANUYDNQCblQa8ROJ2Q3d1s7k)  
**Main Calendar**: `info@splendidmoving.com`  

---

**Last Updated**: February 1, 2026

