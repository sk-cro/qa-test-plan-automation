#!/usr/bin/env python3
"""
Test script to verify the Jira ticket parser functionality.
"""
import sys
import json
from jira_parser import JiraTicketParser

def test_parser():
    """Test the parser with mock data."""
    parser = JiraTicketParser()
    
    # Mock ticket data
    mock_ticket_data = {
        'key': 'MTP-TEST-001',
        'fields': {
            'summary': 'Test CTA Button Experiment',
            'description': '''
Primary metric: Click-through Rate

[NEW] Conversion Rate
[NEW] Time on Page

Requirements:
- Add new CTA button to homepage
- Change button color from red to blue
- Update mobile layout for better visibility
- A/B test with 50/50 traffic split

Custom attributes:
- Button Position: Top-right
- Button Size: Large

Internal notes:
- PGM requested additional bounce rate tracking
- Consider adding scroll depth metric
            ''',
            'labels': ['web', 'experiment', 'cta', 'homepage']
        }
    }
    
    # Test individual parsing functions
    print("🧪 Testing Jira Parser Components")
    print("=" * 50)
    
    # Test platform extraction
    platform = parser._extract_platform_from_labels(['web', 'experiment'])
    print(f"✅ Platform detected: {platform}")
    
    # Test metrics extraction
    metrics = parser._extract_metrics(mock_ticket_data['fields']['description'], {})
    print(f"✅ Primary metric: {metrics['primary']}")
    print(f"✅ Additional metrics: {metrics['additional']}")
    
    # Test custom attributes
    custom_attrs = parser._extract_custom_attributes(
        mock_ticket_data['fields']['description'], 
        {}
    )
    print(f"✅ Custom attributes: {custom_attrs}")
    
    # Test requirements
    requirements = parser._extract_requirements(mock_ticket_data['fields']['description'])
    print(f"✅ Requirements extracted: {len(requirements)} characters")
    
    print("\n🎉 Parser test completed successfully!")

if __name__ == '__main__':
    test_parser()
