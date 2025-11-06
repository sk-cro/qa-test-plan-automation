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
    
    def customize_sheet_with_goals(self, sheet_id: str, tab_name: str, goals: List[str]) -> int:
        """
        Customize a sheet by inserting goals into the specified tab.
        
        Args:
            sheet_id (str): ID of the Google Sheet to customize.
            tab_name (str): Name of the tab to customize (e.g., "[Optimizely] QA Pass 1").
            goals (list): List of goal strings to insert.
            
        Returns:
            int: Number of additional rows inserted (beyond placeholder capacity).
            
        Raises:
            Exception: If customization fails.
        """
        try:
            self.initialize_service()
            logger.info(f"Starting customization of sheet {sheet_id}, tab: {tab_name}")
            
            if not goals:
                logger.info("No goals to insert, skipping customization")
                return 0
            
            # Filter out empty goals
            goals = [g.strip() for g in goals if g.strip()]
            if not goals:
                logger.info("No non-empty goals after filtering, skipping customization")
                return 0
            
            # Find the tab ID; if missing, try to resolve by token only (no auto-creation)
            tab_id = self._get_tab_id(sheet_id, tab_name)
            if tab_id is None:
                # Try token-based resolution (e.g., "[Monetate]")
                token = self._extract_platform_token(tab_name)
                if token:
                    resolved_title, resolved_id = self._find_platform_tab_by_token(sheet_id, token)
                    if resolved_id is not None:
                        logger.info(f"Resolved requested tab '{tab_name}' to existing tab '{resolved_title}' (id={resolved_id})")
                        tab_name = resolved_title
                        tab_id = resolved_id
                
            if tab_id is None:
                # Still not found — clearly report available tabs to guide template updates
                available_titles = self._list_tab_titles(sheet_id)
                logger.error(
                    f"Tab '{tab_name}' not found in sheet; available tabs: {available_titles}"
                )
                raise Exception(f"Tab '{tab_name}' not found in sheet")
            
            # Determine starting row per platform
            platform_token = self._extract_platform_token(tab_name).lower()
            start_row_by_platform = {
                '[monetate]': 23,
                '[vwo]': 26,
                '[convert]': 27,
                '[optimizely]': 28,
            }
            start_row = start_row_by_platform.get(platform_token, 28)
            num_goals = len(goals)
            placeholder_capacity = 3  # existing placeholder rows in each platform tab
            rows_to_insert = max(0, num_goals - placeholder_capacity)
            logger.info(
                f"Preparing space for {num_goals} goals at row {start_row} with {placeholder_capacity} placeholders; inserting {rows_to_insert} additional row(s)"
            )
            
            # Insert only rows beyond placeholder capacity
            if rows_to_insert > 0:
                requests = [{
                    'insertDimension': {
                        'range': {
                            'sheetId': tab_id,
                            'dimension': 'ROWS',
                            'startIndex': (start_row - 1) + placeholder_capacity,
                            'endIndex': (start_row - 1) + placeholder_capacity + rows_to_insert
                        }
                    }
                }]
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={'requests': requests}
                ).execute()
                logger.info(f"Inserted {rows_to_insert} additional row(s) after placeholders")
            else:
                logger.info("No additional rows inserted; placeholders cover all goals")
            
            # Copy formats, formulas, and validations from the template row (start_row)
            # into the C:L columns for all goal rows so columns behave as expected
            copy_source = {
                'sheetId': tab_id,
                'startRowIndex': start_row - 1,
                'endRowIndex': start_row,  # single row
                'startColumnIndex': 2,     # column C (0-based)
                'endColumnIndex': 12       # column L exclusive
            }
            copy_destination = {
                'sheetId': tab_id,
                'startRowIndex': start_row - 1,
                'endRowIndex': start_row - 1 + num_goals,
                'startColumnIndex': 2,
                'endColumnIndex': 12
            }

            copy_requests = [
                { 'copyPaste': { 'source': copy_source, 'destination': copy_destination, 'pasteType': 'PASTE_FORMAT', 'pasteOrientation': 'NORMAL' } },
                { 'copyPaste': { 'source': copy_source, 'destination': copy_destination, 'pasteType': 'PASTE_DATA_VALIDATION', 'pasteOrientation': 'NORMAL' } },
                { 'copyPaste': { 'source': copy_source, 'destination': copy_destination, 'pasteType': 'PASTE_CONDITIONAL_FORMATTING', 'pasteOrientation': 'NORMAL' } },
                { 'copyPaste': { 'source': copy_source, 'destination': copy_destination, 'pasteType': 'PASTE_FORMULA', 'pasteOrientation': 'NORMAL' } },
            ]

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={'requests': copy_requests}
            ).execute()
            logger.info("Copied C:L formats/validations/formulas to goal rows")

            # Now insert the goal content into Column B
            range_name = f"'{tab_name}'!B{start_row}:B{start_row + num_goals - 1}"
            logger.info(f"Inserting goal content into {range_name}")
            
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
            
            logger.info(f"Successfully inserted {num_goals} goals into {tab_name} starting at row {start_row}")
            return rows_to_insert
            
        except Exception as e:
            logger.error(f"Failed to customize sheet {sheet_id}: {e}")
            raise
    
    def customize_sheet_with_custom_attributes(self, sheet_id: str, tab_name: str, custom_attributes: List[str], start_row: int = 34) -> bool:
        """
        Customize a sheet by inserting custom attributes into the specified tab.
        
        This method is specifically designed for Optimizely tickets to insert Custom attributes
        starting at row 34 (separate from Goals which start at row 28).
        
        Args:
            sheet_id (str): ID of the Google Sheet to customize.
            tab_name (str): Name of the tab to customize (e.g., "[Optimizely] QA Pass 1").
            custom_attributes (list): List of custom attribute strings to insert.
            start_row (int): Starting row number (default: 34 for Custom attributes).
            
        Returns:
            bool: True if customization was successful.
            
        Raises:
            Exception: If customization fails.
        """
        try:
            self.initialize_service()
            logger.info(f"Starting custom attributes customization of sheet {sheet_id}, tab: {tab_name}, start_row: {start_row}")
            
            # Validate start_row
            if start_row < 1:
                logger.warning(f"Invalid start_row {start_row}, using default 34")
                start_row = 34
            
            if not custom_attributes:
                logger.info("No custom attributes to insert, skipping customization")
                return True
            
            # Filter out empty custom attributes
            custom_attributes = [ca.strip() for ca in custom_attributes if ca.strip()]
            if not custom_attributes:
                logger.info("No non-empty custom attributes after filtering, skipping customization")
                return True
            
            # Find the tab ID; if missing, try to resolve by token only (no auto-creation)
            tab_id = self._get_tab_id(sheet_id, tab_name)
            if tab_id is None:
                # Try token-based resolution (e.g., "[Optimizely]")
                token = self._extract_platform_token(tab_name)
                if token:
                    resolved_title, resolved_id = self._find_platform_tab_by_token(sheet_id, token)
                    if resolved_id is not None:
                        logger.info(f"Resolved requested tab '{tab_name}' to existing tab '{resolved_title}' (id={resolved_id})")
                        tab_name = resolved_title
                        tab_id = resolved_id
                
            if tab_id is None:
                # Still not found — clearly report available tabs to guide template updates
                available_titles = self._list_tab_titles(sheet_id)
                logger.error(
                    f"Tab '{tab_name}' not found in sheet; available tabs: {available_titles}"
                )
                raise Exception(f"Tab '{tab_name}' not found in sheet")
            
            # Warn if not Optimizely tab (but still proceed)
            platform_token = self._extract_platform_token(tab_name).lower()
            if '[optimizely]' not in platform_token:
                logger.warning(f"Custom attributes should only be used for Optimizely tabs, but tab is: {tab_name}")
            
            num_attributes = len(custom_attributes)
            placeholder_capacity = 3  # existing placeholder rows in each platform tab
            rows_to_insert = max(0, num_attributes - placeholder_capacity)
            logger.info(
                f"Preparing space for {num_attributes} custom attributes at row {start_row} with {placeholder_capacity} placeholders; inserting {rows_to_insert} additional row(s)"
            )
            
            # Insert only rows beyond placeholder capacity
            if rows_to_insert > 0:
                requests = [{
                    'insertDimension': {
                        'range': {
                            'sheetId': tab_id,
                            'dimension': 'ROWS',
                            'startIndex': (start_row - 1) + placeholder_capacity,
                            'endIndex': (start_row - 1) + placeholder_capacity + rows_to_insert
                        }
                    }
                }]
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={'requests': requests}
                ).execute()
                logger.info(f"Inserted {rows_to_insert} additional row(s) after placeholders for custom attributes")
            else:
                logger.info("No additional rows inserted; placeholders cover all custom attributes")
            
            # Copy formats, formulas, and validations from the template row (start_row)
            # into the C:L columns for all custom attribute rows so columns behave as expected
            copy_source = {
                'sheetId': tab_id,
                'startRowIndex': start_row - 1,
                'endRowIndex': start_row,  # single row
                'startColumnIndex': 2,     # column C (0-based)
                'endColumnIndex': 12       # column L exclusive
            }
            copy_destination = {
                'sheetId': tab_id,
                'startRowIndex': start_row - 1,
                'endRowIndex': start_row - 1 + num_attributes,
                'startColumnIndex': 2,
                'endColumnIndex': 12
            }

            copy_requests = [
                { 'copyPaste': { 'source': copy_source, 'destination': copy_destination, 'pasteType': 'PASTE_FORMAT', 'pasteOrientation': 'NORMAL' } },
                { 'copyPaste': { 'source': copy_source, 'destination': copy_destination, 'pasteType': 'PASTE_DATA_VALIDATION', 'pasteOrientation': 'NORMAL' } },
                { 'copyPaste': { 'source': copy_source, 'destination': copy_destination, 'pasteType': 'PASTE_CONDITIONAL_FORMATTING', 'pasteOrientation': 'NORMAL' } },
                { 'copyPaste': { 'source': copy_source, 'destination': copy_destination, 'pasteType': 'PASTE_FORMULA', 'pasteOrientation': 'NORMAL' } },
            ]

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={'requests': copy_requests}
            ).execute()
            logger.info("Copied C:L formats/validations/formulas to custom attribute rows")

            # Now insert the custom attribute content into Column B
            range_name = f"'{tab_name}'!B{start_row}:B{start_row + num_attributes - 1}"
            logger.info(f"Inserting custom attribute content into {range_name}")
            
            # Prepare the values - each custom attribute goes into its own row
            values = [[attr] for attr in custom_attributes]
            
            body = {
                'values': values
            }
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Successfully inserted {num_attributes} custom attributes into {tab_name} starting at row {start_row}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to customize sheet {sheet_id} with custom attributes: {e}")
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

    def _extract_platform_token(self, tab_title: str) -> str:
        """Return the bracketed platform token (e.g., "[Monetate]") from a tab title if present."""
        try:
            if not tab_title:
                return ""
            start = tab_title.find('[')
            end = tab_title.find(']')
            if start != -1 and end != -1 and end > start:
                return tab_title[start:end+1]
            return ""
        except Exception:
            return ""

    def _find_platform_tab_by_token(self, sheet_id: str, token: str):
        """Find an existing tab whose title contains the given token (case-insensitive)."""
        spreadsheet = self.sheets_service.spreadsheets().get(
            spreadsheetId=sheet_id,
            includeGridData=False
        ).execute()
        for sheet in spreadsheet.get('sheets', []):
            title = sheet.get('properties', {}).get('title', '')
            if token and token.lower() in title.lower():
                return title, sheet.get('properties', {}).get('sheetId')
        return None, None

    def _list_tab_titles(self, sheet_id: str):
        spreadsheet = self.sheets_service.spreadsheets().get(
            spreadsheetId=sheet_id,
            includeGridData=False
        ).execute()
        return [s.get('properties', {}).get('title', '') for s in spreadsheet.get('sheets', [])]

    def prune_platform_tabs(self, sheet_id: str, selected_platform_tab: str) -> bool:
        """
        Delete all platform-specific tabs except the selected one and always keep
        the "Complexity & Risk" tab.
        
        Args:
            sheet_id (str): Spreadsheet ID.
            selected_platform_tab (str): The tab title to keep, e.g., "[Optimizely] QA Pass 1".
        
        Returns:
            bool: True if pruning completed successfully (no-op counts as success).
        """
        try:
            self.initialize_service()
            logger.info(f"Pruning platform tabs in sheet {sheet_id}; keeping '{selected_platform_tab}' and 'Complexity & Risk'")

            # Known platform tokens and typical titles
            platform_tokens = [
                "[Optimizely]",
                "[Convert]",
                "[VWO]",
                "[Monetate]",
            ]

            # Derive a robust identifier for the selected platform
            selected_token = None
            for token in platform_tokens:
                if token.lower() in selected_platform_tab.lower():
                    selected_token = token
                    break

            # Fetch spreadsheet metadata
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=sheet_id,
                includeGridData=False
            ).execute()

            sheets = spreadsheet.get('sheets', [])
            delete_requests = []

            # Determine if the selected platform tab actually exists; if not, skip pruning
            selected_exists = False
            for sheet in sheets:
                title = sheet.get('properties', {}).get('title', '')
                if title == selected_platform_tab or (
                    selected_token and selected_token.lower() in title.lower()
                ):
                    selected_exists = True
                    break

            if not selected_exists:
                logger.warning(
                    f"Selected platform tab '{selected_platform_tab}' not found; skipping platform tab pruning to avoid deleting all tabs"
                )
                return True

            for sheet in sheets:
                props = sheet.get('properties', {})
                title = props.get('title')
                sheet_id_to_delete = props.get('sheetId')

                # Never delete the selected platform tab or the Complexity & Risk tab
                if title == selected_platform_tab or title == "Complexity & Risk":
                    continue

                # Delete any other platform tabs we recognize via token matching
                is_platform_tab = any(token.lower() in title.lower() for token in platform_tokens)
                is_selected_platform_tab = selected_token and (selected_token.lower() in title.lower())

                if is_platform_tab and not is_selected_platform_tab:
                    logger.info(f"Scheduling deletion of tab '{title}' (id={sheet_id_to_delete})")
                    delete_requests.append({
                        'deleteSheet': {
                            'sheetId': sheet_id_to_delete
                        }
                    })

            if not delete_requests:
                logger.info("No platform tabs to delete; pruning is a no-op")
                return True

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={'requests': delete_requests}
            ).execute()

            logger.info(f"Successfully pruned {len(delete_requests)} platform tab(s)")
            return True

        except HttpError as e:
            logger.error(f"Failed to prune platform tabs: {e}")
            raise Exception(f"Failed to prune platform tabs: {e}")
        except Exception as e:
            logger.error(f"Unexpected error pruning platform tabs: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting tab ID: {e}")
            raise

