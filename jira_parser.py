"""
Jira ticket data parser module.
Extracts platform and goals from Jira tickets.
"""
import logging
import re
from typing import List, Optional

from jira_client import JiraClient

# Set up logging
logger = logging.getLogger(__name__)


class JiraTicketParser:
    """Parses Jira ticket data to extract information for sheet customization."""
    
    def __init__(self):
        """Initialize the parser with Jira client."""
        self.jira_client = JiraClient()
    
    def extract_platform_from_labels(self, issue_key: str) -> str:
        """
        Extract platform from Jira issue labels.
        
        Args:
            issue_key (str): The Jira issue key (e.g., "MTP-1234").
            
        Returns:
            str: Tab name matching the platform ("[Optimizely] QA Pass 1", "[Convert] QA Pass 1", or "[VWO] QA Pass 1").
                 Defaults to "[Optimizely] QA Pass 1" if no match found.
        """
        try:
            logger.info(f"Extracting platform from labels for issue: {issue_key}")
            
            # Get the issue data
            issue_data = self.jira_client.get_issue(issue_key)
            labels = issue_data.get('fields', {}).get('labels', [])
            
            # Check for exact matches in labels (case-insensitive)
            for label in labels:
                label_lower = label.lower().strip()
                
                if label_lower == 'convert':
                    logger.info(f"Found Convert platform from label: {label}")
                    return "[Convert] QA Pass 1"
                elif label_lower == 'optimizely':
                    logger.info(f"Found Optimizely platform from label: {label}")
                    return "[Optimizely] QA Pass 1"
                elif label_lower == 'vwo':
                    logger.info(f"Found VWO platform from label: {label}")
                    return "[VWO] QA Pass 1"
            
            # No match found, default to Optimizely
            logger.info(f"No platform label found, defaulting to [Optimizely] QA Pass 1")
            return "[Optimizely] QA Pass 1"
            
        except Exception as e:
            logger.error(f"Error extracting platform from labels: {e}")
            # Default to Optimizely on error
            return "[Optimizely] QA Pass 1"
    
    def parse_goals_field(self, issue_key: str) -> List[str]:
        """
        Parse the Goals field from a Jira issue into numbered sections.
        
        Args:
            issue_key (str): The Jira issue key (e.g., "MTP-1234").
            
        Returns:
            list: List of goal strings, each containing all content for that numbered goal.
                  Returns empty list if no Goals field found or empty.
        """
        try:
            logger.info(f"Parsing Goals field for issue: {issue_key}")
            
            # Get the Goals field text
            goals_text = self.jira_client.get_goals_field(issue_key)
            
            if not goals_text or not goals_text.strip():
                logger.info(f"No Goals field found or empty for issue: {issue_key}")
                return []
            
            # Parse numbered goals
            # Pattern: Number followed by period and space, then all content until next number or end
            goals = []
            
            # Find all goal patterns
            # Looking for patterns like "1. ", "2. ", "3. ", etc.
            goal_pattern = r'(\d+\.\s+.+?)(?=\d+\.\s+|$)'
            matches = re.findall(goal_pattern, goals_text, re.DOTALL)
            
            for match in matches:
                goal_text = match.strip()
                if goal_text:
                    goals.append(goal_text)
            
            logger.info(f"Parsed {len(goals)} goals from Goals field")
            return goals
            
        except Exception as e:
            logger.error(f"Error parsing Goals field: {e}")
            return []
