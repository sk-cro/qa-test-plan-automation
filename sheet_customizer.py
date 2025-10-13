"""
Google Sheets customization module.
Handles dynamic content insertion and formatting based on Jira ticket data.
"""
import logging
from typing import Dict, List, Any

from googleapiclient.errors import HttpError
from config import Config
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
    
    def customize_qa_test_plan(self, sheet_id: str, ticket_data: Dict[str, Any]) -> bool:
        """
        Customize a QA test plan sheet based on ticket data.
        
        Args:
            sheet_id (str): ID of the Google Sheet to customize.
            ticket_data (dict): Parsed ticket data from JiraTicketParser.
            
        Returns:
            bool: True if customization was successful.
            
        Raises:
            Exception: If customization fails.
        """
        try:
            self.initialize_service()
            logger.info(f"Starting customization of sheet {sheet_id}")
            
            # Get sheet metadata to understand structure
            sheet_metadata = self._get_sheet_metadata(sheet_id)
            
            # Step 1: Handle platform-specific tab management
            self._manage_platform_tabs(sheet_id, ticket_data['platform'], sheet_metadata)
            
            # Step 2: Handle custom attributes (delete/add rows)
            if not ticket_data['has_custom_attributes']:
                self._delete_custom_attribute_rows(sheet_id)
            else:
                self._add_custom_attributes(sheet_id, ticket_data['custom_attributes'])
            
            # Step 3: Insert metrics into Metrics sections
            self._insert_metrics(sheet_id, ticket_data['primary_metric'], ticket_data['additional_metrics'])
            
            # Step 4: Insert requirements into Spec Requirements
            self._insert_requirements(sheet_id, ticket_data['requirements'])
            
            # Step 5: Handle internal notes (future enhancement)
            if ticket_data['internal_notes']:
                self._add_internal_notes(sheet_id, ticket_data['internal_notes'])
            
            logger.info(f"Successfully customized sheet {sheet_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to customize sheet {sheet_id}: {e}")
            raise
    
    def _get_sheet_metadata(self, sheet_id: str) -> Dict[str, Any]:
        """
        Get metadata about the sheet structure.
        
        Args:
            sheet_id (str): Sheet ID.
            
        Returns:
            dict: Sheet metadata including sheet names and ranges.
        """
        try:
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=sheet_id,
                includeGridData=False
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            sheet_info = {}
            
            for sheet in sheets:
                sheet_props = sheet.get('properties', {})
                sheet_name = sheet_props.get('title', '')
                sheet_info[sheet_name] = {
                    'id': sheet_props.get('sheetId'),
                    'gridProperties': sheet_props.get('gridProperties', {}),
                    'hidden': sheet_props.get('hidden', False)
                }
            
            logger.info(f"Retrieved metadata for {len(sheet_info)} sheets")
            return sheet_info
            
        except HttpError as e:
            logger.error(f"Failed to get sheet metadata: {e}")
            raise
    
    def _manage_platform_tabs(self, sheet_id: str, platform: str, sheet_metadata: Dict[str, Any]):
        """
        Manage platform-specific tabs based on ticket platform.
        
        Args:
            sheet_id (str): Sheet ID.
            platform (str): Platform name (Web, Mobile, etc.).
            sheet_metadata (dict): Sheet metadata.
        """
        try:
            logger.info(f"Managing tabs for platform: {platform}")
            
            # Map platform names to sheet names
            platform_sheet_mapping = {
                'Web': ['[Optimizely] QA Pass 1', '[Convert] QA Pass 1', '[VWO] QA Pass 1'],
                'Mobile': ['[Optimizely] QA Pass 1', '[Convert] QA Pass 1', '[VWO] QA Pass 1'],
                'Backend': ['[Optimizely] QA Pass 1', '[Convert] QA Pass 1', '[VWO] QA Pass 1'],
                'Email': ['[Convert] QA Pass 1'],
                'Push': ['[Convert] QA Pass 1'],
                'SMS': ['[Convert] QA Pass 1']
            }
            
            # Default to keeping all QA Pass sheets for now
            tabs_to_keep = ['Values', 'Complexity & Risk'] + platform_sheet_mapping.get(platform, ['[Optimizely] QA Pass 1', '[Convert] QA Pass 1', '[VWO] QA Pass 1'])
            
            # Hide/delete non-relevant tabs
            requests = []
            for sheet_name, sheet_info in sheet_metadata.items():
                # Always keep hidden sheets and complexity & risk
                if sheet_info.get('hidden', False) or 'Complexity' in sheet_name or 'Values' in sheet_name:
                    continue
                    
                # Check if this sheet should be kept
                should_keep = any(tab.lower() in sheet_name.lower() for tab in tabs_to_keep)
                
                if not should_keep:
                    # Hide this tab
                    requests.append({
                        'updateSheetProperties': {
                            'properties': {
                                'sheetId': sheet_info['id'],
                                'hidden': True
                            },
                            'fields': 'hidden'
                        }
                    })
                    logger.info(f"Will hide sheet: {sheet_name}")
            
            if requests:
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={'requests': requests}
                ).execute()
                logger.info(f"Hidden {len(requests)} non-relevant tabs")
            
        except Exception as e:
            logger.error(f"Failed to manage platform tabs: {e}")
            raise
    
    def _delete_custom_attribute_rows(self, sheet_id: str):
        """
        Delete rows related to custom attributes when none exist.
        
        Args:
            sheet_id (str): Sheet ID.
        """
        try:
            logger.info("Deleting custom attribute rows (no custom attributes)")
            
            # Rows to delete: 17, 30, 31, 54, 55
            rows_to_delete = [17, 30, 31, 54, 55]
            
            # Sort in descending order to avoid index shifting
            rows_to_delete.sort(reverse=True)
            
            requests = []
            for row in rows_to_delete:
                requests.append({
                    'deleteDimension': {
                        'range': {
                            'sheetId': 0,  # Assuming main sheet
                            'dimension': 'ROWS',
                            'startIndex': row - 1,  # Convert to 0-based index
                            'endIndex': row
                        }
                    }
                })
            
            if requests:
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={'requests': requests}
                ).execute()
                logger.info(f"Deleted {len(requests)} custom attribute rows")
            
        except Exception as e:
            logger.error(f"Failed to delete custom attribute rows: {e}")
            raise
    
    def _add_custom_attributes(self, sheet_id: str, custom_attributes: List[str]):
        """
        Add custom attributes to the Custom Attribute section.
        
        Args:
            sheet_id (str): Sheet ID.
            custom_attributes (list): List of custom attributes.
        """
        try:
            logger.info(f"Adding {len(custom_attributes)} custom attributes")
            
            # Find the Custom Attribute section and insert attributes
            # Try to insert into the main QA Pass sheets
            qa_sheets = ['[Optimizely] QA Pass 1', '[Convert] QA Pass 1', '[VWO] QA Pass 1']
            
            for i, attribute in enumerate(custom_attributes):
                attribute_inserted = False
                
                for sheet_name in qa_sheets:
                    # Try multiple possible ranges for custom attributes
                    possible_base_ranges = [f'{sheet_name}!B16', f'{sheet_name}!B15', f'{sheet_name}!B17', f'{sheet_name}!C16']
                    
                    for base_range in possible_base_ranges:
                        try:
                            # Extract the column and base row from the range
                            column = base_range.split('!')[1].split(':')[0][0]  # Get column letter
                            base_row = int(base_range.split('!')[1].split(':')[0][1:])  # Get base row number
                            
                            range_name = f"{sheet_name}!{column}{base_row + i}"
                            
                            self.sheets_service.spreadsheets().values().update(
                                spreadsheetId=sheet_id,
                                range=range_name,
                                valueInputOption='RAW',
                                body={'values': [[attribute]]}
                            ).execute()
                            
                            logger.info(f"Custom attribute '{attribute}' inserted at {range_name}")
                            attribute_inserted = True
                            break
                            
                        except HttpError as e:
                            if "Unable to parse range" in str(e):
                                logger.info(f"Range {range_name} not valid, trying next")
                                continue
                            else:
                                raise
                    
                    if attribute_inserted:
                        break
                
                if not attribute_inserted:
                    logger.warning(f"Could not insert custom attribute '{attribute}', skipping")
            
            logger.info("Successfully added custom attributes")
            
        except Exception as e:
            logger.error(f"Failed to add custom attributes: {e}")
            raise
    
    def _insert_metrics(self, sheet_id: str, primary_metric: str, additional_metrics: List[str]):
        """
        Insert metrics into the Metrics sections.
        
        Args:
            sheet_id (str): Sheet ID.
            primary_metric (str): Primary metric name.
            additional_metrics (list): Additional metrics with [NEW] prefix.
        """
        try:
            logger.info(f"Inserting metrics - Primary: {primary_metric}, Additional: {additional_metrics}")
            
            # Insert primary metric
            if primary_metric:
                # Find empty cells in Metrics sections and insert
                # This needs to be customized based on your template structure
                metrics_ranges = [
                    'Sheet1!D5',  # Example range for primary metric
                    'Sheet1!D10',  # Example range for variation 1
                    'Sheet1!D15'   # Example range for variation 2
                ]
                
                for range_name in metrics_ranges:
                    self.sheets_service.spreadsheets().values().update(
                        spreadsheetId=sheet_id,
                        range=range_name,
                        valueInputOption='RAW',
                        body={'values': [[primary_metric]]}
                    ).execute()
            
            # Insert additional metrics with [NEW] prefix
            for i, metric in enumerate(additional_metrics):
                new_metric = f"[NEW] {metric}"
                # Insert in next available space
                range_name = f"Sheet1!D{20 + i}"  # Adjust based on template
                
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=sheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': [[new_metric]]}
                ).execute()
            
            # If more than 2 metrics, add additional rows
            if len(additional_metrics) > 2:
                self._add_additional_metric_rows(sheet_id, len(additional_metrics) - 2)
            
            logger.info("Successfully inserted metrics")
            
        except Exception as e:
            logger.error(f"Failed to insert metrics: {e}")
            raise
    
    def _add_additional_metric_rows(self, sheet_id: str, num_rows: int):
        """
        Add additional rows for metrics when needed.
        
        Args:
            sheet_id (str): Sheet ID.
            num_rows (int): Number of additional rows to add.
        """
        try:
            logger.info(f"Adding {num_rows} additional rows for metrics")
            
            requests = []
            for i in range(num_rows):
                requests.append({
                    'insertDimension': {
                        'range': {
                            'sheetId': 0,
                            'dimension': 'ROWS',
                            'startIndex': 20 + i,  # Adjust based on template
                            'endIndex': 21 + i
                        }
                    }
                })
            
            if requests:
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={'requests': requests}
                ).execute()
                logger.info(f"Added {num_rows} additional rows")
            
        except Exception as e:
            logger.error(f"Failed to add additional metric rows: {e}")
            raise
    
    def _insert_requirements(self, sheet_id: str, requirements: str):
        """
        Insert experiment requirements into Spec Requirements section.
        
        Args:
            sheet_id (str): Sheet ID.
            requirements (str): Requirements text.
        """
        try:
            logger.info("Inserting requirements into Spec Requirements section")
            
            # Format requirements text (limit to reasonable length)
            formatted_requirements = self._format_requirements_text(requirements)
            
            # Insert into Spec Requirements section
            # Try to insert into the main QA Pass sheets
            qa_sheets = ['[Optimizely] QA Pass 1', '[Convert] QA Pass 1', '[VWO] QA Pass 1']
            
            try:
                range_updated = False
                
                for sheet_name in qa_sheets:
                    # Try common ranges for requirements
                    possible_ranges = [f'{sheet_name}!B25', f'{sheet_name}!B20', f'{sheet_name}!B30', f'{sheet_name}!C25']
                    
                    for range_name in possible_ranges:
                        try:
                            self.sheets_service.spreadsheets().values().update(
                                spreadsheetId=sheet_id,
                                range=range_name,
                                valueInputOption='RAW',
                                body={'values': [[formatted_requirements]]}
                            ).execute()
                            logger.info(f"Requirements inserted at {range_name}")
                            range_updated = True
                            break
                        except HttpError as e:
                            if "Unable to parse range" in str(e):
                                logger.info(f"Range {range_name} not valid, trying next")
                                continue
                            else:
                                raise
                    
                    if range_updated:
                        break
                
                if not range_updated:
                    logger.warning("Could not find valid range for requirements, skipping")
                    
            except Exception as e:
                logger.error(f"Failed to insert requirements: {e}")
                raise
            
            # If requirements are too long, add more rows
            if len(formatted_requirements.split('\n')) > 3:
                self._expand_requirements_section(sheet_id, formatted_requirements)
            
            logger.info("Successfully inserted requirements")
            
        except Exception as e:
            logger.error(f"Failed to insert requirements: {e}")
            raise
    
    def _format_requirements_text(self, requirements: str) -> str:
        """
        Format requirements text for insertion into sheet.
        
        Args:
            requirements (str): Raw requirements text.
            
        Returns:
            str: Formatted requirements text.
        """
        # Clean up the text
        formatted = requirements.strip()
        
        # Limit length to prevent sheet overflow
        if len(formatted) > 500:
            formatted = formatted[:497] + "..."
        
        # Replace multiple newlines with single newlines
        import re
        formatted = re.sub(r'\n+', '\n', formatted)
        
        return formatted
    
    def _expand_requirements_section(self, sheet_id: str, requirements: str):
        """
        Expand the requirements section if content is too long.
        
        Args:
            sheet_id (str): Sheet ID.
            requirements (str): Requirements text.
        """
        try:
            lines = requirements.split('\n')
            additional_lines = len(lines) - 3
            
            if additional_lines > 0:
                logger.info(f"Expanding requirements section by {additional_lines} lines")
                
                # Add rows after the requirements section
                requests = []
                for i in range(additional_lines):
                    requests.append({
                        'insertDimension': {
                            'range': {
                                'sheetId': 0,
                                'dimension': 'ROWS',
                                'startIndex': 25 + i,  # Adjust based on template
                                'endIndex': 26 + i
                            }
                        }
                    })
                
                if requests:
                    self.sheets_service.spreadsheets().batchUpdate(
                        spreadsheetId=sheet_id,
                        body={'requests': requests}
                    ).execute()
                    
                    # Insert the additional lines
                    for i, line in enumerate(lines[3:], 1):
                        range_name = f"Sheet1!B{25 + i}"
                        self.sheets_service.spreadsheets().values().update(
                            spreadsheetId=sheet_id,
                            range=range_name,
                            valueInputOption='RAW',
                            body={'values': [[line]]}
                        ).execute()
                
                logger.info("Successfully expanded requirements section")
            
        except Exception as e:
            logger.error(f"Failed to expand requirements section: {e}")
            raise
    
    def _add_internal_notes(self, sheet_id: str, internal_notes: str):
        """
        Add internal notes section (future enhancement).
        
        Args:
            sheet_id (str): Sheet ID.
            internal_notes (str): Internal notes text.
        """
        try:
            logger.info("Adding internal notes section")
            
            # This is a placeholder for future enhancement
            # You can implement this based on your specific needs
            
            logger.info("Internal notes functionality ready for future implementation")
            
        except Exception as e:
            logger.error(f"Failed to add internal notes: {e}")
            raise
