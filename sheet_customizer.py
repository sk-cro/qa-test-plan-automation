"""
Google Sheets customization module.
Handles dynamic content insertion based on Jira ticket data.
"""
import logging
from typing import List

from googleapiclient.errors import HttpError

from google_auth import GoogleAuthManager

# Set up logging
logger = logging.getLogger(__name__)


class SheetCustomizer:
    """Customizes Google Sheets based on parsed Jira ticket data."""
    
    def __init__(self):
        """Initialize the sheet customizer."""
        self.auth_manager = GoogleAuthManager()
        self.sheets_service = None
    
    def initialize_service(self):
        """Initialize Google Sheets service."""
        if not self.sheets_service:
            self.sheets_service = self.auth_manager.get_sheets_service()
        logger.info("Google Sheets service initialized for customization")
    
    def customize_sheet_with_goals(self, sheet_id: str, tab_name: str, goals: List[str]) -> bool:
        """
        Customize a sheet by inserting goals into the specified tab.
        
        Args:
            sheet_id (str): ID of the Google Sheet to customize.
            tab_name (str): Name of the tab to customize (e.g., "[Optimizely] QA Pass 1").
            goals (list): List of goal strings to insert.
            
        Returns:
            bool: True if customization was successful.
            
        Raises:
            Exception: If customization fails.
        """
        try:
            self.initialize_service()
            logger.info(f"Starting customization of sheet {sheet_id}, tab: {tab_name}")
            
            if not goals:
                logger.info("No goals to insert, skipping customization")
                return True
            
            # Find the tab ID
            tab_id = self._get_tab_id(sheet_id, tab_name)
            if tab_id is None:
                logger.error(f"Tab '{tab_name}' not found in sheet")
                raise Exception(f"Tab '{tab_name}' not found in sheet")
            
            # Insert rows starting at row 28
            num_goals = len(goals)
            logger.info(f"Inserting {num_goals} rows starting at row 28")
            
            # Insert all rows at once using batchUpdate
            requests = [{
                'insertDimension': {
                    'range': {
                        'sheetId': tab_id,
                        'dimension': 'ROWS',
                        'startIndex': 27,  # Row 28 (0-based index)
                        'endIndex': 27 + num_goals
                    }
                }
            }]
            
            # Execute the insert
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={'requests': requests}
            ).execute()
            
            logger.info(f"Successfully inserted {num_goals} rows")
            
            # Now insert the goal content into Column B
            range_name = f"'{tab_name}'!B28:B{27 + num_goals}"
            
            # Prepare the values - each goal goes into its own row
            values = [[goal] for goal in goals]
            
            body = {
                'values': values
            }
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Successfully inserted {num_goals} goals into {tab_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to customize sheet {sheet_id}: {e}")
            raise
    
    def _get_tab_id(self, sheet_id: str, tab_name: str) -> int:
        """
        Get the tab ID for a given tab name.
        
        Args:
            sheet_id (str): The spreadsheet ID.
            tab_name (str): The name of the tab.
            
        Returns:
            int: The tab ID, or None if not found.
        """
        try:
            logger.info(f"Looking for tab: {tab_name}")
            
            # Get spreadsheet metadata
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=sheet_id,
                includeGridData=False
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            
            # Find the matching tab
            for sheet in sheets:
                sheet_props = sheet.get('properties', {})
                if sheet_props.get('title') == tab_name:
                    tab_id = sheet_props.get('sheetId')
                    logger.info(f"Found tab ID: {tab_id} for '{tab_name}'")
                    return tab_id
            
            logger.error(f"Tab '{tab_name}' not found")
            return None
            
        except HttpError as e:
            logger.error(f"Failed to get tab ID: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting tab ID: {e}")
            raise

