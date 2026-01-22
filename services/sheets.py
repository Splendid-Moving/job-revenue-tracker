from services.auth import get_service
import config
from datetime import datetime

class SheetsService:
    def __init__(self):
        self.service = get_service('sheets', 'v4')
        self.spreadsheet_id = config.TARGET_SPREADSHEET_ID # "1USAoTNsUKIzg4XKzyeQANUYDNQCblQa8ROJ2Q3d1s7k"
        
    def get_monthly_sheet_name(self):
        """Returns the sheet name for current month, e.g., 'Jan 2026'"""
        return datetime.now().strftime("%b %Y")

    def ensure_sheet_exists(self, sheet_name):
        """Checks if sheet exists, creates it if not."""
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        existing_sheets = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
        
        if sheet_name not in existing_sheets:
            print(f"Sheet '{sheet_name}' not found. Creating it...")
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id, 
                body=body
            ).execute()
            
            # Optional: Add headers
            header = ["Date", "Job ID", "Summary", "Status", "Total Revenue", "Net Revenue", "Payment Type", "Submitted At", "Source"]
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption='USER_ENTERED',
                body={'values': [header]}
            ).execute()

    def append_job_data(self, job_report_list):
        """
        Appends a list of job reports to the month's sheet.
        """
        if not job_report_list:
            return

        sheet_name = self.get_monthly_sheet_name()
        self.ensure_sheet_exists(sheet_name)
        
        range_name = f"'{sheet_name}'!A1" 
        value_input_option = 'USER_ENTERED'
        
        body = {
            'values': job_report_list
        }
        
        result = self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body=body
        ).execute()
        
        print(f"{result.get('updates').get('updatedCells')} cells appended to {sheet_name}.")
        return result

    def check_date_exists(self, date_str):
        """
        Checks if the given date string exists in Column A of the current month's sheet.
        Returns True if found, False otherwise.
        """
        try:
            sheet_name = self.get_monthly_sheet_name()
            # Ensure sheet exists first (it might not if this is the first run of the month)
            # But checking existence is expensive if we do full ensure.
            # Let's just try to read. If sheet doesn't exist, date definitely doesn't exist.
            
            # Read Column A (Dates)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A:A"
            ).execute()
            
            rows = result.get('values', [])
            # Flatten list of lists: [['Date'], ['2026-01-20'], ...] -> ['Date', '2026-01-20']
            dates = [row[0] for row in rows if row]
            
            return date_str in dates
            
        except Exception as e:
            # If sheet doesn't exist or other error, assume not duplicate
            # print(f"Check date error (likely sheet not found yet): {e}")
            return False

# Singleton-ish helper if needed or just instantiate
