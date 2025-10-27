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
    
    def get_goals_field(self, issue_key):
        """
        Extract the Goals field from a Jira issue.
        
        Args:
            issue_key (str): The Jira issue key (e.g., "MTP-1234").
            
        Returns:
            str: The Goals field text, or empty string if not found.
        """
        try:
            logger.info(f"Fetching Goals field for issue: {issue_key}")
            
            # Get the issue data
            issue_data = self.get_issue(issue_key)
            fields = issue_data.get('fields', {})
            
            # Look for the Goals custom field (customfield_10040)
            goals_field = fields.get('customfield_10040')
            
            if goals_field:
                logger.info(f"Found Goals field in customfield_10040")
                # Log the raw field structure
                logger.info(f"Goals field type: {type(goals_field)}")
                if isinstance(goals_field, dict):
                    logger.info(f"Goals field keys: {list(goals_field.keys())[:5]}")
                
                # Handle different field types
                if isinstance(goals_field, str):
                    return goals_field
                elif isinstance(goals_field, dict):
                    # Handle ADF document format
                    if 'content' in goals_field:
                        converted_text = self._convert_adf_to_text(goals_field)
                        logger.info(f"ADF converted (first 200 chars): {converted_text[:200]}")
                        return converted_text
                    return str(goals_field)
                else:
                    return str(goals_field) if goals_field else ''
            
            logger.warning(f"No Goals field found for issue: {issue_key}")
            return ''
            
        except Exception as e:
            logger.error(f"Error fetching Goals field: {e}")
            return ''
    
    def _convert_adf_to_text(self, adf_document, depth=0):
        """
        Convert Atlassian Document Format (ADF) to plain text.
        
        Args:
            adf_document (dict): ADF document structure.
            depth (int): Current nesting depth.
            
        Returns:
            str: Plain text representation.
        """
        try:
            if not isinstance(adf_document, dict):
                return str(adf_document)
            
            content = adf_document.get('content', [])
            if not content:
                return ''
            
            text_parts = []
            
            for node in content:
                text_parts.append(self._extract_text_from_adf_node(node, depth))
            
            return '\n'.join(filter(None, text_parts))
            
        except Exception as e:
            logger.warning(f"Failed to convert ADF to text: {e}")
            return str(adf_document)
    
    def _extract_text_from_adf_node(self, node, depth=0):
        """
        Extract text from a single ADF node.
        
        Args:
            node (dict): ADF node.
            depth (int): Current nesting depth.
            
        Returns:
            str: Extracted text.
        """
        try:
            if not isinstance(node, dict):
                return ''
            
            node_type = node.get('type', '')
            content = node.get('content', [])
            text = node.get('text', '')
            
            # Handle different node types
            if node_type == 'paragraph':
                if content:
                    paragraph_text = ''.join(self._extract_text_from_adf_node(child, depth) for child in content)
                    return paragraph_text
                else:
                    return text or ''
            
            elif node_type == 'text':
                return text or ''
            
            elif node_type == 'heading':
                level = node.get('attrs', {}).get('level', 1)
                heading_text = ''.join(self._extract_text_from_adf_node(child, depth) for child in content) if content else text or ''
                return f"{'#' * level} {heading_text}"
            
            elif node_type == 'bulletList':
                items = []
                for item in content:
                    item_content = item.get('content', [])
                    item_text = ''.join(self._extract_text_from_adf_node(child, depth) for child in item_content)
                    if item_text:
                        items.append(f"- {item_text}")
                return '\n'.join(items)
            
            elif node_type == 'orderedList':
                items = []
                for index, item in enumerate(content, start=1):
                    item_content = item.get('content', [])
                    item_text = ''.join(self._extract_text_from_adf_node(child, depth) for child in item_content)
                    if item_text:
                        items.append(f"{index}. {item_text}")
                return '\n'.join(items)
            
            elif node_type == 'listItem':
                # Get the parent's order to determine numbering
                # This is a simplified approach - just extract content
                item_text = ''.join(self._extract_text_from_adf_node(child) for child in content)
                return item_text
            
            elif node_type == 'hardBreak':
                return '\n'
            
            else:
                # For unknown node types, try to extract text from content
                if content:
                    return ''.join(self._extract_text_from_adf_node(child, depth) for child in content)
                else:
                    return text or ''
                    
        except Exception as e:
            logger.warning(f"Failed to extract text from ADF node: {e}")
            return ''

