import os

# Google API Configuration
SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = [
    'https://www.googleapis.com/auth/calendar',  # Full access (for updating events)
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/forms.responses.readonly',
    'https://www.googleapis.com/auth/drive', # Needed for creating file in folder
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/spreadsheets' # For linking to sheets
]

# Client Email extracted from service_account.json
# Client Email: moving-tracker-server@ad-report-automation-484101.iam.gserviceaccount.com

# Calendar Configuration
CALENDAR_ID = 'info@splendidmoving.com' # User's shared calendar


TARGET_SPREADSHEET_ID = "1USAoTNsUKIzg4XKzyeQANUYDNQCblQa8ROJ2Q3d1s7k"

# Email Configuration
TARGET_EMAIL = 'info@splendidmoving.com'

# Calendar Event Color to Source Mapping
# Color IDs from Google Calendar API
COLOR_SOURCE_MAP = {
    '6': 'Yelp',        # #ffb878 (orange)
    '2': 'Google LSA',  # #7ae7bf (teal/mint)
    # Add more color mappings here as needed
    # To find color IDs, check: https://developers.google.com/calendar/api/v3/reference/colors
}

