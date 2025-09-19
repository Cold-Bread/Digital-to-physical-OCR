
import os
import logging
from typing import List, Optional, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache

logger = logging.getLogger(__name__)

# Disable file cache to prevent the warning message
class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content

# Update these constants with your values
SPREADSHEET_ID = '1_gLQUeWhE6QamZY0CV-n7P06dzq7zRTzTYDPfXvjqC0'  # Get this from your Google Sheets URL
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']



def get_sheets_service() -> Any:
    """Create and return Google Sheets service object"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=SCOPES
        )
        # Use memory cache instead of file cache
        service = build('sheets', 'v4', credentials=credentials, cache=MemoryCache())
        logger.debug("Google Sheets service created successfully.")
        return service.spreadsheets()
    
    except Exception as e:
        logger.error(f"Error creating Google Sheets service with credentials file '{CREDENTIALS_FILE}': {e}")
        return None

def read_sheet_range(range_name: str) -> Optional[List[List[str]]]:
    """Read data from specified range in the spreadsheet"""
    sheets = get_sheets_service()
    if not sheets:
        logger.error("Could not obtain Google Sheets service. Aborting read operation.")
        return None
    try:
        result = sheets.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        values = result.get('values', [])
        logger.info(f"Successfully read {len(values)} rows from range '{range_name}' in spreadsheet '{SPREADSHEET_ID}'.")
        return values
    
    except Exception as e:
        logger.error(f"Error reading range '{range_name}' from spreadsheet '{SPREADSHEET_ID}': {e}")
        return None

def update_sheet_range(range_name: str, values: List[List[str]]) -> bool:
    """Update data in specified range in the spreadsheet"""
    sheets = get_sheets_service()
    if not sheets:
        logger.error("Could not obtain Google Sheets service. Aborting update operation.")
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
        updated_rows = result.get('updatedRows', 0)
        logger.info(f"Updated range '{range_name}' in spreadsheet '{SPREADSHEET_ID}' with {len(values)} rows. Google API updated {updated_rows} rows. Response: {result}")
        return True
    
    except Exception as e:
        logger.error(f"Error updating range '{range_name}' in spreadsheet '{SPREADSHEET_ID}': {e}")
        return False
