"""
Google Sheets and Drive operations module.
Handles creating copies of templates, renaming sheets, and moving files.
"""
import logging
from googleapiclient.errors import HttpError

from config import Config
from google_auth import GoogleAuthManager

# Set up logging
logger = logging.getLogger(__name__)


class GoogleSheetsManager:
    """Manages Google Sheets and Drive operations."""
    
    def __init__(self):
        """Initialize the Sheets manager."""
        self.auth_manager = GoogleAuthManager()
        self.drive_service = None
        self.sheets_service = None
    
    def initialize_services(self):
        """Initialize Google Drive and Sheets services."""
        try:
            if not self.drive_service:
                self.drive_service = self.auth_manager.get_drive_service()
            if not self.sheets_service:
                self.sheets_service = self.auth_manager.get_sheets_service()
            logger.info("Google services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google services: {e}")
            raise
    
    def copy_template_sheet(self, template_id=None):
        """
        Create a copy of the template Google Sheet.
        
        Args:
            template_id (str, optional): Template sheet ID. Uses config default if not provided.
            
        Returns:
            str: ID of the newly created sheet.
            
        Raises:
            Exception: If copying fails.
        """
        if not self.drive_service:
            self.initialize_services()
        
        template_id = template_id or Config.TEMPLATE_SHEET_ID
        
        try:
            logger.info(f"Copying template sheet: {template_id}")
            
            # Copy the file
            file_metadata = {
                'name': 'QA Test Plan (Copy)'  # Temporary name, will be renamed
            }
            
            copied_file = self.drive_service.files().copy(
                fileId=template_id,
                body=file_metadata
            ).execute()
            
            new_sheet_id = copied_file.get('id')
            logger.info(f"Successfully created copy with ID: {new_sheet_id}")
            
            return new_sheet_id
            
        except HttpError as e:
            logger.error(f"Failed to copy template sheet: {e}")
            raise Exception(f"Failed to copy template sheet: {e}")
        except Exception as e:
            logger.error(f"Unexpected error copying template: {e}")
            raise
    
    def rename_sheet(self, sheet_id, new_name):
        """
        Rename a Google Sheet.
        
        Args:
            sheet_id (str): ID of the sheet to rename.
            new_name (str): New name for the sheet.
            
        Returns:
            bool: True if successful.
            
        Raises:
            Exception: If renaming fails.
        """
        if not self.drive_service:
            self.initialize_services()
        
        try:
            logger.info(f"Renaming sheet {sheet_id} to '{new_name}'")
            
            file_metadata = {
                'name': new_name
            }
            
            self.drive_service.files().update(
                fileId=sheet_id,
                body=file_metadata
            ).execute()
            
            logger.info(f"Successfully renamed sheet to '{new_name}'")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to rename sheet: {e}")
            raise Exception(f"Failed to rename sheet: {e}")
        except Exception as e:
            logger.error(f"Unexpected error renaming sheet: {e}")
            raise
    
    def move_sheet_to_folder(self, sheet_id, folder_id=None):
        """
        Move a Google Sheet to a specific folder.
        
        Args:
            sheet_id (str): ID of the sheet to move.
            folder_id (str, optional): Destination folder ID. Uses config default if not provided.
            
        Returns:
            bool: True if successful.
            
        Raises:
            Exception: If moving fails.
        """
        if not self.drive_service:
            self.initialize_services()
        
        folder_id = folder_id or Config.DESTINATION_FOLDER_ID
        
        try:
            logger.info(f"Moving sheet {sheet_id} to folder {folder_id}")
            
            # Retrieve the existing parents to remove
            file = self.drive_service.files().get(
                fileId=sheet_id,
                fields='parents'
            ).execute()
            
            previous_parents = ",".join(file.get('parents', []))
            
            # Move the file to the new folder
            self.drive_service.files().update(
                fileId=sheet_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
            logger.info(f"Successfully moved sheet to folder {folder_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to move sheet to folder: {e}")
            raise Exception(f"Failed to move sheet to folder: {e}")
        except Exception as e:
            logger.error(f"Unexpected error moving sheet: {e}")
            raise
    
    def get_sheet_url(self, sheet_id):
        """
        Generate the URL for a Google Sheet.
        
        Args:
            sheet_id (str): ID of the sheet.
            
        Returns:
            str: URL to the Google Sheet.
        """
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        logger.info(f"Generated sheet URL: {url}")
        return url
    
    def create_qa_test_plan(self, jira_issue_key):
        """
        Create a complete QA test plan sheet for a Jira issue.
        
        This is the main workflow method that:
        1. Copies the template
        2. Renames it with the Jira issue key
        3. Moves it to the destination folder
        
        Args:
            jira_issue_key (str): The Jira issue key (e.g., "MTP-1234").
            
        Returns:
            dict: Dictionary containing 'sheet_id' and 'sheet_url'.
            
        Raises:
            Exception: If any step fails.
        """
        try:
            logger.info(f"Creating QA test plan for {jira_issue_key}")
            
            # Step 1: Copy the template
            new_sheet_id = self.copy_template_sheet()
            
            # Step 2: Rename the sheet
            new_name = f"{jira_issue_key} - QA Test Plan"
            self.rename_sheet(new_sheet_id, new_name)
            
            # Step 3: Move to destination folder
            self.move_sheet_to_folder(new_sheet_id)
            
            # Step 4: Get the URL
            sheet_url = self.get_sheet_url(new_sheet_id)
            
            logger.info(f"Successfully created QA test plan: {sheet_url}")
            
            return {
                'sheet_id': new_sheet_id,
                'sheet_url': sheet_url
            }
            
        except Exception as e:
            logger.error(f"Failed to create QA test plan: {e}")
            raise

