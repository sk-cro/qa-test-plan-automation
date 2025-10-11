"""
Jira API client module.
Handles communication with Jira REST API.
"""
import logging
import requests
from requests.auth import HTTPBasicAuth

from config import Config

# Set up logging
logger = logging.getLogger(__name__)


class JiraClient:
    """Client for interacting with Jira REST API."""
    
    def __init__(self):
        """Initialize the Jira client."""
        self.base_url = Config.JIRA_URL.rstrip('/')
        self.username = Config.JIRA_USERNAME
        self.api_token = Config.JIRA_API_TOKEN
        self.auth = HTTPBasicAuth(self.username, self.api_token)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def validate_credentials(self):
        """
        Validate Jira credentials by making a test API call.
        
        Returns:
            bool: True if credentials are valid.
            
        Raises:
            Exception: If credentials are invalid or connection fails.
        """
        try:
            logger.info("Validating Jira credentials")
            url = f"{self.base_url}/rest/api/3/myself"
            
            response = requests.get(
                url,
                headers=self.headers,
                auth=self.auth,
                timeout=10
            )
            
            response.raise_for_status()
            logger.info("Jira credentials validated successfully")
            return True
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("Invalid Jira credentials")
                raise Exception("Invalid Jira credentials")
            logger.error(f"HTTP error validating credentials: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Jira: {e}")
            raise
    
    def get_issue(self, issue_key):
        """
        Get details of a Jira issue.
        
        Args:
            issue_key (str): The Jira issue key (e.g., "MTP-1234").
            
        Returns:
            dict: Issue data from Jira API.
            
        Raises:
            Exception: If issue cannot be retrieved.
        """
        try:
            logger.info(f"Fetching Jira issue: {issue_key}")
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
            
            response = requests.get(
                url,
                headers=self.headers,
                auth=self.auth,
                timeout=10
            )
            
            response.raise_for_status()
            issue_data = response.json()
            
            logger.info(f"Successfully fetched issue: {issue_key}")
            return issue_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Issue not found: {issue_key}")
                raise Exception(f"Issue not found: {issue_key}")
            logger.error(f"HTTP error fetching issue: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch issue: {e}")
            raise
    
    def add_comment(self, issue_key, comment_text):
        """
        Add a comment to a Jira issue.
        
        Args:
            issue_key (str): The Jira issue key (e.g., "MTP-1234").
            comment_text (str): The comment text to add.
            
        Returns:
            dict: Comment data from Jira API.
            
        Raises:
            Exception: If comment cannot be added.
        """
        try:
            logger.info(f"Adding comment to issue: {issue_key}")
            url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
            
            payload = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment_text
                                }
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                auth=self.auth,
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            comment_data = response.json()
            
            logger.info(f"Successfully added comment to issue: {issue_key}")
            return comment_data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error adding comment: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"Failed to add comment to Jira: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to add comment: {e}")
            raise
    
    def post_qa_plan_comment(self, issue_key, sheet_url):
        """
        Post a comment with the QA test plan URL to a Jira issue.
        
        Args:
            issue_key (str): The Jira issue key (e.g., "MTP-1234").
            sheet_url (str): URL to the Google Sheet.
            
        Returns:
            dict: Comment data from Jira API.
            
        Raises:
            Exception: If comment cannot be added.
        """
        comment_text = f"QA Test Plan has been created: {sheet_url}"
        return self.add_comment(issue_key, comment_text)

