"""
Google API authentication module.
Handles OAuth 2.0 authentication for Google Drive and Sheets APIs.
"""
import os
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import Config

# Set up logging
logger = logging.getLogger(__name__)


class GoogleAuthManager:
    """Manages Google API authentication and service creation."""
    
    def __init__(self):
        """Initialize the authentication manager."""
        self.credentials = None
        self.scopes = Config.GOOGLE_SCOPES
        self.credentials_file = Config.GOOGLE_CREDENTIALS_FILE
        self.token_file = Config.GOOGLE_TOKEN_FILE
    
    def authenticate(self):
        """
        Authenticate with Google APIs using OAuth 2.0.
        
        Returns:
            Credentials: Authenticated credentials object.
            
        Raises:
            FileNotFoundError: If credentials.json file is not found.
            Exception: If authentication fails.
        """
        try:
            # Check if credentials are in environment variable (for Railway/serverless)
            if os.getenv('GOOGLE_TOKEN_JSON'):
                import json
                logger.info("Loading credentials from environment variable")
                token_data = json.loads(os.getenv('GOOGLE_TOKEN_JSON'))
                self.credentials = Credentials.from_authorized_user_info(token_data, self.scopes)
                if self.credentials and self.credentials.valid:
                    logger.info("Successfully loaded valid credentials from environment")
                    return self.credentials
            
            # Check if we have existing valid credentials in file
            if os.path.exists(self.token_file):
                logger.info(f"Loading credentials from {self.token_file}")
                self.credentials = Credentials.from_authorized_user_file(
                    self.token_file, self.scopes
                )
            
            # If credentials don't exist or are invalid, authenticate
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("Refreshing expired credentials")
                    self.credentials.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        raise FileNotFoundError(
                            f"Credentials file not found: {self.credentials_file}. "
                            "Please download it from Google Cloud Console."
                        )
                    
                    logger.info("Starting new OAuth 2.0 flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes
                    )
                    self.credentials = flow.run_local_server(port=0)
                
                # Save credentials for future use
                logger.info(f"Saving credentials to {self.token_file}")
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
            
            logger.info("Successfully authenticated with Google APIs")
            return self.credentials
            
        except FileNotFoundError as e:
            logger.error(f"Credentials file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def get_drive_service(self):
        """
        Create and return a Google Drive service object.
        
        Returns:
            Resource: Google Drive API service object.
            
        Raises:
            Exception: If service creation fails.
        """
        try:
            if not self.credentials:
                self.authenticate()
            
            logger.info("Creating Google Drive service")
            service = build('drive', 'v3', credentials=self.credentials)
            return service
            
        except HttpError as e:
            logger.error(f"Failed to create Drive service: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating Drive service: {e}")
            raise
    
    def get_sheets_service(self):
        """
        Create and return a Google Sheets service object.
        
        Returns:
            Resource: Google Sheets API service object.
            
        Raises:
            Exception: If service creation fails.
        """
        try:
            if not self.credentials:
                self.authenticate()
            
            logger.info("Creating Google Sheets service")
            service = build('sheets', 'v4', credentials=self.credentials)
            return service
            
        except HttpError as e:
            logger.error(f"Failed to create Sheets service: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating Sheets service: {e}")
            raise

