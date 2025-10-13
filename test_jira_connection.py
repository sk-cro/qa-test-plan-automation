#!/usr/bin/env python3
"""
Test Jira API connection and authentication.
"""
import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

load_dotenv()

def test_jira_connection():
    """Test Jira API connection."""
    print("🔍 Testing Jira API Connection")
    print("=" * 40)
    
    # Get credentials
    jira_url = os.getenv('JIRA_URL', 'https://crometrics.atlassian.net/')
    username = os.getenv('JIRA_USERNAME', 'sean.khan@crometrics.com')
    api_token = os.getenv('JIRA_API_TOKEN')
    
    if not api_token:
        print("❌ JIRA_API_TOKEN not found in environment variables")
        return False
    
    print(f"✅ Jira URL: {jira_url}")
    print(f"✅ Username: {username}")
    print(f"✅ API Token: {'*' * (len(api_token) - 4) + api_token[-4:]}")
    
    # Test basic connection
    try:
        print("\n🧪 Testing basic API connection...")
        url = f"{jira_url.rstrip('/')}/rest/api/3/myself"
        auth = HTTPBasicAuth(username, api_token)
        headers = {'Accept': 'application/json'}
        
        response = requests.get(url, auth=auth, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Connection successful!")
            print(f"✅ Logged in as: {user_data.get('displayName', 'Unknown')}")
            print(f"✅ Account ID: {user_data.get('accountId', 'Unknown')}")
            return True
        else:
            print(f"❌ Connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_specific_issue(issue_key):
    """Test fetching a specific issue."""
    print(f"\n🧪 Testing issue fetch for {issue_key}...")
    
    jira_url = os.getenv('JIRA_URL', 'https://crometrics.atlassian.net/')
    username = os.getenv('JIRA_USERNAME', 'sean.khan@crometrics.com')
    api_token = os.getenv('JIRA_API_TOKEN')
    
    try:
        url = f"{jira_url.rstrip('/')}/rest/api/3/issue/{issue_key}"
        auth = HTTPBasicAuth(username, api_token)
        headers = {'Accept': 'application/json'}
        
        response = requests.get(url, auth=auth, headers=headers, timeout=10)
        
        if response.status_code == 200:
            issue_data = response.json()
            print(f"✅ Issue {issue_key} found!")
            print(f"✅ Summary: {issue_data.get('fields', {}).get('summary', 'Unknown')}")
            print(f"✅ Status: {issue_data.get('fields', {}).get('status', {}).get('name', 'Unknown')}")
            return True
        elif response.status_code == 404:
            print(f"❌ Issue {issue_key} not found (404)")
            return False
        else:
            print(f"❌ Issue fetch failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Issue fetch error: {e}")
        return False

if __name__ == '__main__':
    # Test connection
    if test_jira_connection():
        # Test specific issue
        test_specific_issue('MTP-71')
    else:
        print("\n❌ Cannot proceed with issue test - basic connection failed")
