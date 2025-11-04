import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class SheetsManager:
    """Handles all Google Sheets operations"""

    def __init__(self, config):
        # Support both URL and name (URL is more reliable)
        self.sheet_url = os.getenv('GOOGLE_SHEET_URL', '')
        self.sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Job_Application_Tracker')
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.config = config
        self.columns = config['sheets']['columns']
        self.default_status = config['sheets']['default_status']

        # Check if credentials file exists
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"Google credentials file not found: {self.credentials_file}\n"
                "Please download your service account credentials from Google Cloud Console"
            )

        # Initialize Google Sheets client
        self.client = None
        self.worksheet = None
        self._connect()

    def _connect(self):
        """Connect to Google Sheets"""
        try:
            # gspread requires both Sheets and Drive scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )

            self.client = gspread.authorize(creds)

            # Open the spreadsheet - try URL first (more reliable), then name
            try:
                if self.sheet_url:
                    # Open by URL (most reliable method)
                    spreadsheet = self.client.open_by_url(self.sheet_url)
                else:
                    # Fall back to opening by name
                    spreadsheet = self.client.open(self.sheet_name)

                self.worksheet = spreadsheet.sheet1  # Use first sheet

            except gspread.SpreadsheetNotFound:
                if self.sheet_url:
                    raise Exception(
                        f"Spreadsheet not found at URL: {self.sheet_url}\n"
                        "Please check the URL and make sure it's shared with your service account email."
                    )
                else:
                    raise Exception(
                        f"Spreadsheet '{self.sheet_name}' not found.\n"
                        "Opening by name often fails. Please use GOOGLE_SHEET_URL in .env instead.\n"
                        "Share the spreadsheet with your service account, then add:\n"
                        "GOOGLE_SHEET_URL=<your-spreadsheet-url>"
                    )

            # Initialize headers if sheet is empty
            self._initialize_headers()

        except Exception as e:
            raise Exception(f"Failed to connect to Google Sheets: {e}")

    def _initialize_headers(self):
        """Initialize column headers if sheet is empty"""
        try:
            existing_headers = self.worksheet.row_values(1)

            if not existing_headers or existing_headers == ['']:
                # Sheet is empty, add headers
                self.worksheet.update('A1', [self.columns])
                print(f"✓ Initialized sheet headers: {', '.join(self.columns)}")

        except Exception as e:
            print(f"Warning: Could not initialize headers: {e}")

    def check_duplicate(self, company_name, position_title):
        """Check if job already exists in the sheet"""
        try:
            all_values = self.worksheet.get_all_values()

            # Skip header row
            for row in all_values[1:]:
                if len(row) >= 2:
                    existing_company = row[0].strip().lower()
                    existing_position = row[1].strip().lower()

                    if (existing_company == company_name.strip().lower() and
                        existing_position == position_title.strip().lower()):
                        return True

            return False

        except Exception as e:
            print(f"Warning: Could not check for duplicates: {e}")
            return False

    def append_job(self, extracted_data, job_url='', personalized_message=''):
        """Append job data to the sheet"""
        try:
            # Check for duplicates
            if self.check_duplicate(
                extracted_data.get('company_name', ''),
                extracted_data.get('position_title', '')
            ):
                print(f"⚠ Job already exists: {extracted_data.get('company_name')} - {extracted_data.get('position_title')}")
                return False

            # Extract founders data (max 2 founders)
            founders_list = extracted_data.get('founders', [])

            # Founder 1
            founder1_name = 'Not specified'
            founder1_linkedin = 'N/A'
            if len(founders_list) >= 1:
                founder1_name = founders_list[0].get('name', 'Not specified')
                founder1_linkedin = founders_list[0].get('linkedin', 'N/A')

            # Founder 2
            founder2_name = 'Not specified'
            founder2_linkedin = 'N/A'
            if len(founders_list) >= 2:
                founder2_name = founders_list[1].get('name', 'Not specified')
                founder2_linkedin = founders_list[1].get('linkedin', 'N/A')

            # Prepare row data according to new column structure
            row_data = [
                extracted_data.get('company_name', 'N/A'),
                extracted_data.get('position_title', 'N/A'),
                extracted_data.get('location', 'N/A'),
                extracted_data.get('employment_type', 'Full-time'),
                job_url if job_url else 'N/A',  # Job Description Link
                extracted_data.get('salary_range', 'Not specified'),
                extracted_data.get('equity_range', 'Not specified'),
                founder1_name,  # Founder 1
                founder1_linkedin,  # Founder 1 LinkedIn
                founder2_name,  # Founder 2
                founder2_linkedin,  # Founder 2 LinkedIn
                extracted_data.get('required_experience', 'Not specified'),
                extracted_data.get('visa_sponsorship', 'Not specified'),
                '',  # Match % (leave empty for manual entry)
                personalized_message if personalized_message else '',  # Personalized Message
                datetime.now().strftime('%Y-%m-%d'),  # Application Date
                self.default_status  # Status
            ]

            # Append to sheet
            self.worksheet.append_row(row_data)
            return True

        except Exception as e:
            print(f"Error appending to sheet: {e}")
            return False

    def get_sheet_info(self):
        """Get basic information about the sheet"""
        try:
            all_values = self.worksheet.get_all_values()
            return {
                'total_rows': len(all_values),
                'total_jobs': len(all_values) - 1,  # Excluding header
                'sheet_name': self.sheet_name
            }
        except Exception as e:
            print(f"Error getting sheet info: {e}")
            return None
