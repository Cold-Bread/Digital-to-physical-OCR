from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache
import os

# Disable file cache to prevent the warning message
class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content

# Update these constants with your values
SPREADSHEET_ID = ''  # Get this from your Google Sheets URL
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    """Create and return Google Sheets service object"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=SCOPES
        )
        # Use memory cache instead of file cache
        service = build('sheets', 'v4', credentials=credentials, cache=MemoryCache())
        return service.spreadsheets()
    except Exception as e:
        print(f"Error creating sheets service: {e}")
        return None

def read_sheet_range(range_name):
    """Read data from specified range in the spreadsheet"""
    sheets = get_sheets_service()
    if not sheets:
        return None
    
    try:
        result = sheets.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"Error reading sheet: {e}")
        return None

def update_sheet_range(range_name, values):
    """Update data in specified range in the spreadsheet"""
    sheets = get_sheets_service()
    if not sheets:
        return False
    
    try:
        body = {
            'values': values
        }
        result = sheets.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        return True
    except Exception as e:
        print(f"Error updating sheet: {e}")
        return False
