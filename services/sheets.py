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
        
        # After appending, update the dashboard
        self.ensure_dashboard_sheet()
        
        return result

    def ensure_dashboard_sheet(self):
        """
        Creates/Updates a 'Summary' sheet with a dynamic dashboard formula.
        """
        try:
            dashboard_name = "Summary"
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            existing_sheets = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
            
            if dashboard_name not in existing_sheets:
                body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': dashboard_name,
                                'index': 0 # Make it the first tab
                            }
                        }
                    }]
                }
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id, 
                    body=body
                ).execute()

            # Update Formulas for the current month
            current_month = self.get_monthly_sheet_name()
            
            # Dashboard Title
            title = [[f"Monthly Revenue Breakdown ({current_month})"], []]
            
            # The QUERY formula aggregates by Source (Col I) where Status (Col D) is 'Yes'
            # A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8, I=9
            formula = f"=QUERY('{current_month}'!A:I, \"select I, sum(E), sum(F) where D = 'Yes' group by I label I 'Source', sum(E) 'Total Revenue', sum(F) 'Net Revenue'\", 1)"
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{dashboard_name}!A1",
                valueInputOption='USER_ENTERED',
                body={'values': title}
            ).execute()

            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{dashboard_name}!A3",
                valueInputOption='USER_ENTERED',
                body={'values': [[formula]]}
            ).execute()
            
        except Exception as e:
            from utils.logger import log_error
            log_error(f"Error updating dashboard: {e}")

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

    def create_job_row(self, date_str, job_id, summary, source):
        """
        Creates a pre-populated row for a job with blank revenue fields.
        Used by the 7 PM pre-population job.
        Returns the row number where the job was inserted.
        """
        sheet_name = self.get_monthly_sheet_name()
        self.ensure_sheet_exists(sheet_name)
        
        # Row: [Date, Job ID, Summary, Status, Total Revenue, Net Revenue, Payment Type, Submitted At, Source]
        # Status, revenues, payment, submitted_at are blank (to be filled by form)
        row = [date_str, job_id, summary, "", "", "", "", "", source]
        
        result = self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption='USER_ENTERED',
            body={'values': [row]}
        ).execute()
        
        # Extract row number from updatedRange (e.g., "'Jan 2026'!A5:I5" -> 5)
        updated_range = result.get('updates', {}).get('updatedRange', '')
        row_num = None
        if updated_range:
            import re
            match = re.search(r'!A(\d+):', updated_range)
            if match:
                row_num = int(match.group(1))
        
        print(f"Created pre-populated row for job {job_id} at row {row_num}")
        return row_num

    def get_job_by_id(self, job_id, sheet_name=None):
        """
        Finds a job row by its Job ID (Column B).
        If sheet_name is None, searches ALL sheets (for cross-month lookups).
        Returns tuple: (row_number, row_data, sheet_name) or (None, None, None) if not found.
        """
        try:
            # Get list of sheets to search
            if sheet_name:
                sheets_to_search = [sheet_name]
            else:
                # Get all sheet names from spreadsheet
                spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
                sheets_to_search = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
                # Exclude dashboard/summary sheets
                sheets_to_search = [s for s in sheets_to_search if s != 'Summary']
            
            for current_sheet in sheets_to_search:
                try:
                    result = self.service.spreadsheets().values().get(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"'{current_sheet}'!A:I"
                    ).execute()
                    
                    rows = result.get('values', [])
                    for idx, row in enumerate(rows):
                        # Column B (index 1) is Job ID
                        if len(row) > 1 and row[1] == job_id:
                            return (idx + 1, row, current_sheet)  # 1-indexed row number + sheet name
                except Exception:
                    continue  # Sheet might be empty or inaccessible
            
            return (None, None, None)
            
        except Exception as e:
            print(f"Error fetching job by ID: {e}")
            return (None, None, None)

    def update_job_row(self, job_id, status, total_rev, net_rev, payment_type):
        """
        Updates an existing job row with form submission data.
        Automatically finds the correct sheet by searching all sheets.
        Returns True on success, False on failure.
        """
        # Find the job across all sheets
        row_num, existing_row, sheet_name = self.get_job_by_id(job_id)
        
        if not row_num:
            print(f"Job {job_id} not found in any sheet")
            return False
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update columns D through H (Status, Total, Net, Payment, Submitted At)
        # D=4, E=5, F=6, G=7, H=8 (1-indexed in Sheets)
        update_range = f"'{sheet_name}'!D{row_num}:H{row_num}"
        update_values = [[status, total_rev, net_rev, payment_type, timestamp]]
        
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=update_range,
            valueInputOption='USER_ENTERED',
            body={'values': update_values}
        ).execute()
        
        print(f"Updated job {job_id} at row {row_num}")
        
        # Update dashboard after changes
        self.ensure_dashboard_sheet()
        
        return True

# Singleton-ish helper if needed or just instantiate
