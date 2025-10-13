"""
Jira ticket data parser module.
Extracts and processes ticket information for QA test plan customization.
"""
import logging
import re
from typing import Dict, List, Optional, Any

from config import Config
from jira_client import JiraClient

# Set up logging
logger = logging.getLogger(__name__)


class JiraTicketParser:
    """Parses Jira ticket data to extract information for QA test plan customization."""
    
    def __init__(self):
        """Initialize the parser with Jira client."""
        self.jira_client = JiraClient()
    
    def parse_ticket_for_qa_plan(self, issue_key: str) -> Dict[str, Any]:
        """
        Parse a Jira ticket and extract all relevant data for QA test plan creation.
        
        Args:
            issue_key (str): The Jira issue key (e.g., "MTP-1234").
            
        Returns:
            dict: Parsed ticket data including platform, metrics, requirements, etc.
            
        Raises:
            Exception: If ticket cannot be retrieved or parsed.
        """
        try:
            logger.info(f"Parsing ticket {issue_key} for QA plan data")
            
            # Get full ticket data from Jira
            ticket_data = self.jira_client.get_issue(issue_key)
            
            # Extract basic information
            parsed_data = {
                'issue_key': issue_key,
                'summary': ticket_data.get('fields', {}).get('summary', ''),
                'description': ticket_data.get('fields', {}).get('description', ''),
                'labels': ticket_data.get('fields', {}).get('labels', []),
                'custom_fields': {},
                'platform': None,
                'primary_metric': None,
                'additional_metrics': [],
                'custom_attributes': [],
                'requirements': '',
                'has_custom_attributes': False,
                'internal_notes': ''
            }
            
            # Parse platform from labels
            parsed_data['platform'] = self._extract_platform_from_labels(parsed_data['labels'])
            
            # Parse custom fields
            parsed_data['custom_fields'] = self._extract_custom_fields(ticket_data)
            
            # Parse metrics from description and custom fields
            metrics = self._extract_metrics(parsed_data['description'], parsed_data['custom_fields'])
            parsed_data['primary_metric'] = metrics.get('primary')
            parsed_data['additional_metrics'] = metrics.get('additional', [])
            
            # Parse custom attributes
            parsed_data['custom_attributes'] = self._extract_custom_attributes(
                parsed_data['description'], 
                parsed_data['custom_fields']
            )
            parsed_data['has_custom_attributes'] = len(parsed_data['custom_attributes']) > 0
            
            # Extract requirements section
            parsed_data['requirements'] = self._extract_requirements(parsed_data['description'])
            
            # Extract internal notes
            parsed_data['internal_notes'] = self._extract_internal_notes(parsed_data['description'])
            
            logger.info(f"Successfully parsed ticket {issue_key}")
            logger.info(f"Platform: {parsed_data['platform']}")
            logger.info(f"Primary metric: {parsed_data['primary_metric']}")
            logger.info(f"Custom attributes: {len(parsed_data['custom_attributes'])}")
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Failed to parse ticket {issue_key}: {e}")
            raise
    
    def _extract_platform_from_labels(self, labels: List[str]) -> Optional[str]:
        """
        Extract experiment platform from ticket labels.
        
        Args:
            labels (list): List of ticket labels.
            
        Returns:
            str or None: The platform name if found.
        """
        platform_keywords = {
            'web': ['web', 'website', 'frontend'],
            'mobile': ['mobile', 'ios', 'android', 'app'],
            'backend': ['backend', 'api', 'server'],
            'email': ['email', 'mail'],
            'push': ['push', 'notification'],
            'sms': ['sms', 'text']
        }
        
        for label in labels:
            label_lower = label.lower()
            for platform, keywords in platform_keywords.items():
                if any(keyword in label_lower for keyword in keywords):
                    logger.info(f"Found platform '{platform}' from label '{label}'")
                    return platform.title()
        
        logger.info("No platform found in labels, defaulting to Web")
        return "Web"  # Default platform
    
    def _extract_custom_fields(self, ticket_data: Dict) -> Dict[str, Any]:
        """
        Extract custom fields from ticket data.
        
        Args:
            ticket_data (dict): Raw ticket data from Jira.
            
        Returns:
            dict: Custom field values.
        """
        custom_fields = {}
        fields = ticket_data.get('fields', {})
        
        # Common custom field patterns
        for key, value in fields.items():
            if key.startswith('customfield_'):
                custom_fields[key] = value
        
        # Look for specific field names in the data
        if 'customfield_10001' in fields:  # Example custom field
            custom_fields['experiment_type'] = fields['customfield_10001']
        
        return custom_fields
    
    def _extract_metrics(self, description: str, custom_fields: Dict) -> Dict[str, List[str]]:
        """
        Extract primary and additional metrics from ticket data.
        
        Args:
            description (str): Ticket description.
            custom_fields (dict): Custom field values.
            
        Returns:
            dict: Dictionary with 'primary' and 'additional' metrics.
        """
        metrics = {'primary': None, 'additional': []}
        
        # Look for [NEW] prefix in description
        new_metrics = re.findall(r'\[NEW\][\s]*([^\n\r\[\]]+)', description, re.IGNORECASE)
        if new_metrics:
            metrics['additional'] = [metric.strip() for metric in new_metrics]
        
        # Look for primary metric indicators
        primary_patterns = [
            r'primary metric[:\s]+([^\n\r]+)',
            r'main metric[:\s]+([^\n\r]+)',
            r'primary KPI[:\s]+([^\n\r]+)'
        ]
        
        for pattern in primary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                metrics['primary'] = match.group(1).strip()
                break
        
        # If no primary metric found, use first [NEW] metric as primary
        if not metrics['primary'] and metrics['additional']:
            metrics['primary'] = metrics['additional'][0]
            metrics['additional'] = metrics['additional'][1:]
        
        return metrics
    
    def _extract_custom_attributes(self, description: str, custom_fields: Dict) -> List[str]:
        """
        Extract custom attributes from ticket data.
        
        Args:
            description (str): Ticket description.
            custom_fields (dict): Custom field values.
            
        Returns:
            list: List of custom attributes.
        """
        attributes = []
        
        # Look for custom attribute patterns in description
        attribute_patterns = [
            r'custom attribute[:\s]+([^\n\r]+)',
            r'additional attribute[:\s]+([^\n\r]+)',
            r'custom field[:\s]+([^\n\r]+)'
        ]
        
        for pattern in attribute_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            attributes.extend([attr.strip() for attr in matches])
        
        # Check custom fields for attributes
        for key, value in custom_fields.items():
            if value and isinstance(value, str) and len(value.strip()) > 0:
                attributes.append(value.strip())
        
        return list(set(attributes))  # Remove duplicates
    
    def _extract_requirements(self, description: str) -> str:
        """
        Extract experiment requirements from ticket description.
        
        Args:
            description (str): Ticket description.
            
        Returns:
            str: Formatted requirements text.
        """
        # Look for requirements section
        requirements_patterns = [
            r'requirements[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'experiment requirements[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'changes[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'specification[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\Z)'
        ]
        
        for pattern in requirements_patterns:
            match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
            if match:
                requirements = match.group(1).strip()
                # Clean up the requirements text
                requirements = re.sub(r'\n+', '\n', requirements)
                return requirements
        
        # If no specific section found, use first paragraph as requirements
        paragraphs = [p.strip() for p in description.split('\n\n') if p.strip()]
        if paragraphs:
            return paragraphs[0]
        
        return "No specific requirements found"
    
    def _extract_internal_notes(self, description: str) -> str:
        """
        Extract internal notes from ticket description.
        
        Args:
            description (str): Ticket description.
            
        Returns:
            str: Internal notes text.
        """
        # Look for internal notes section
        notes_patterns = [
            r'internal notes[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'notes[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'additional notes[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\Z)'
        ]
        
        for pattern in notes_patterns:
            match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
