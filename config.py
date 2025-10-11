"""
Configuration management for the QA Test Plan automation application.
All sensitive data should be loaded from environment variables.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()


class Config:
    """Application configuration class."""
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Jira Configuration
    JIRA_URL = os.getenv('JIRA_URL', 'https://crometrics.atlassian.net/')
    JIRA_USERNAME = os.getenv('JIRA_USERNAME', 'sean.khan@crometrics.com')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')  # Must be set in environment
    
    # Google Workspace Configuration
    GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')
    GOOGLE_SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    
    # Google Sheet Template Configuration
    TEMPLATE_SHEET_ID = os.getenv('TEMPLATE_SHEET_ID', '1D8jLAB8SwxCYeBCldsIVCTHSZ9SEsMjbKvbsC5smiiU')
    DESTINATION_FOLDER_ID = os.getenv('DESTINATION_FOLDER_ID', '1ZDG-Gdx9iTc-UFqje2YZtUF3vJya4MeG')
    
    # Application Settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def validate():
        """Validate that all required configuration is present."""
        required_vars = {
            'JIRA_API_TOKEN': Config.JIRA_API_TOKEN,
        }
        
        missing = [key for key, value in required_vars.items() if not value]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True

