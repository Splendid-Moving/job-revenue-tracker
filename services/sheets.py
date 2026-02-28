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
        """Checks if sheet exists, creates it if not.
        Also formatting: Freezes top 2 rows, adds headers and SUM formulas.
        """
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        existing_sheets = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
        
        if sheet_name not in existing_sheets:
            print(f"Sheet '{sheet_name}' not found. Creating it...")
            body = {
                'requests': [
                    {
                        'addSheet': {
                            'properties': {
                                'title': sheet_name,
                                'gridProperties': {
                                    'frozenRowCount': 2
                                }
                            }
                        }
                    }
                ]
            }
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id, 
                body=body
            ).execute()
            
            # Add Headers (Row 1) and Total Formulas (Row 2)
            header = ["Date", "Job ID", "Summary", "Status", "Total Revenue", "Net Revenue", "Payment Type", "Submitted At", "Source"]
            formulas = ["", "", "TOTALS:", "", "=SUM(E3:E)", "=SUM(F3:F)", "", "", ""]
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1:I2",
                valueInputOption='USER_ENTERED',
                body={'values': [header, formulas]}
            ).execute()
            
            # Bold the headers
            format_body = {
                'requests': [{
                    'repeatCell': {
                        'range': {
                            'sheetId': self._get_sheet_id(sheet_name),
                            'startRowIndex': 0,
                            'endRowIndex': 2
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {'bold': True}
                            }
                        },
                        'fields': 'userEnteredFormat.textFormat.bold'
                    }
                }]
            }
            try:
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=format_body
                ).execute()
            except Exception as e:
                print(f"Formatting failed (non-critical): {e}")

    def _get_sheet_id(self, sheet_name):
        """Helper to get sheetId from sheet title"""
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        for s in spreadsheet.get('sheets', []):
            if s['properties']['title'] == sheet_name:
                return s['properties']['sheetId']
        return 0

    def append_job_data(self, job_report_list):
        """
        Appends a list of job reports to the correct month's sheet.
        Derives the sheet from the date in the first row of data.
        """
        if not job_report_list:
            return

        # Derive sheet from the date in the first row (column A) if available
        first_date = job_report_list[0][0] if job_report_list[0] else None
        if first_date:
            try:
                job_date = datetime.strptime(first_date, "%Y-%m-%d")
                sheet_name = job_date.strftime("%b %Y")
            except (ValueError, TypeError):
                sheet_name = self.get_monthly_sheet_name()
        else:
            sheet_name = self.get_monthly_sheet_name()

        self.ensure_sheet_exists(sheet_name)
        
        result = self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption='USER_ENTERED',
            body={'values': job_report_list}
        ).execute()
        
        print(f"{result.get('updates').get('updatedCells')} cells appended to {sheet_name}.")
        
        # After appending, update the dashboard
        self.ensure_dashboard_sheet()
        
        return result


    def ensure_dashboard_sheet(self):
        """
        Creates/Updates a 'Summary' sheet that aggregates totals from ALL monthly sheets.
        """
        try:
            dashboard_name = "Summary"
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheets = spreadsheet.get('sheets', [])
            existing_sheet_titles = [s['properties']['title'] for s in sheets]
            
            # Ensure Summary sheet exists
            if dashboard_name not in existing_sheet_titles:
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

            # Filter for monthly sheets (e.g. "Jan 2026")
            import re
            monthly_sheets = []
            for s in sheets:
                title = s['properties']['title']
                # Match "Mmm YYYY" pattern
                if re.match(r'^[A-Z][a-z]{2} \d{4}$', title):
                    monthly_sheets.append(title)
            
            # Sort sheets chronologically
            try:
                monthly_sheets.sort(key=lambda x: datetime.strptime(x, "%b %Y"))
            except ValueError:
                pass # Keep original order if parsing fails

            # Build Summary Table
            # Header
            summary_data = [
                ["GLOBAL REVENUE HISTORY"],
                ["Month", "Total Revenue", "Net Revenue", "Yelp Revenue", "Google LSA Revenue", "Yelp Jobs", "Google LSA Jobs", "Other Jobs", "Total Jobs"],
            ]
            
            # Rows for each month
            for sheet in monthly_sheets:
                # Using formulas is better so it updates live
                # Monthly sheet columns — E: Total, F: Net, I: Source
                row = [
                    sheet, 
                    f"=SUM('{sheet}'!E3:E)", 
                    f"=SUM('{sheet}'!F3:F)",
                    f"=SUMIF('{sheet}'!I3:I, \"Yelp\", '{sheet}'!E3:E)",
                    f"=SUMIF('{sheet}'!I3:I, \"Google LSA\", '{sheet}'!E3:E)",
                    f"=COUNTIF('{sheet}'!I3:I, \"Yelp\")",
                    f"=COUNTIF('{sheet}'!I3:I, \"Google LSA\")",
                    f"=COUNTA('{sheet}'!B3:B)-COUNTIF('{sheet}'!I3:I, \"Yelp\")-COUNTIF('{sheet}'!I3:I, \"Google LSA\")",
                    f"=COUNTA('{sheet}'!B3:B)",
                ]
                summary_data.append(row)
                
            # Grand Total Row
            summary_data.append(["", "", "", "", "", "", "", "", ""]) # Spacer
            summary_data.append([
                "GRAND TOTAL", 
                f"=SUM(B3:B{len(summary_data)})", 
                f"=SUM(C3:C{len(summary_data)})",
                f"=SUM(D3:D{len(summary_data)})",
                f"=SUM(E3:E{len(summary_data)})",
                f"=SUM(F3:F{len(summary_data)})",
                f"=SUM(G3:G{len(summary_data)})",
                f"=SUM(H3:H{len(summary_data)})",
                f"=SUM(I3:I{len(summary_data)})",
            ])
            
            # Write to Summary Sheet
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{dashboard_name}!A1",
                valueInputOption='USER_ENTERED',
                body={'values': summary_data}
            ).execute()
            
            # Format Summary Sheet
            format_requests = [
                # Bold Header
                {
                    'repeatCell': {
                        'range': {'sheetId': self._get_sheet_id(dashboard_name), 'startRowIndex': 1, 'endRowIndex': 2},
                        'cell': {'userEnteredFormat': {'textFormat': {'bold': True}}},
                        'fields': 'userEnteredFormat.textFormat.bold'
                    }
                },
                # Bold Grand Total
                {
                    'repeatCell': {
                        'range': {'sheetId': self._get_sheet_id(dashboard_name), 'startRowIndex': len(summary_data)-1, 'endRowIndex': len(summary_data)},
                        'cell': {'userEnteredFormat': {'textFormat': {'bold': True}}},
                        'fields': 'userEnteredFormat.textFormat.bold'
                    }
                }
            ]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': format_requests}
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
        Inserts in date-sorted order so reconciled past jobs appear with their date group.
        Returns the row number where the job was inserted.
        """
        import re as _re

        # Derive sheet name from the job's date (handles cross-month reconciliation)
        job_date = datetime.strptime(date_str, "%Y-%m-%d")
        sheet_name = job_date.strftime("%b %Y")
        self.ensure_sheet_exists(sheet_name)

        # Row: [Date, Job ID, Summary, Status, Total Revenue, Net Revenue, Payment Type, Submitted At, Source]
        row = [date_str, job_id, summary, "", None, None, "", "", source]

        # Find the correct insertion point (date-sorted, after header rows 1-2)
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{sheet_name}'!A:A"
        ).execute()
        dates = result.get('values', [])

        # Find insert position: after the last row whose date <= date_str
        # Rows 0,1 are header/totals, data starts at index 2 (sheet row 3)
        insert_idx = len(dates)  # default: append at end
        for i in range(2, len(dates)):
            cell = dates[i][0] if dates[i] else ""
            if cell > date_str:
                insert_idx = i
                break

        sheet_row = insert_idx + 1  # 1-indexed sheet row number
        sheet_id = self._get_sheet_id(sheet_name)

        # Insert a blank row at the correct position
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'requests': [{
                'insertDimension': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'ROWS',
                        'startIndex': insert_idx,   # 0-indexed
                        'endIndex': insert_idx + 1
                    },
                    'inheritFromBefore': False
                }
            }]}
        ).execute()

        # Write data into the newly inserted row
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{sheet_name}'!A{sheet_row}:I{sheet_row}",
            valueInputOption='USER_ENTERED',
            body={'values': [row]}
        ).execute()

        print(f"Created pre-populated row for job {job_id} at row {sheet_row}")
        return sheet_row

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
