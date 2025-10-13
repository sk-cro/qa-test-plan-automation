#!/usr/bin/env python3
"""
Diagnostic tool to identify Jira API issues.
"""
import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

load_dotenv()

def diagnose_jira_api():
    """Diagnose Jira API connection issues."""
    print("🔍 Jira API Diagnostic Tool")
    print("=" * 50)
    
    # Get credentials
    jira_url = os.getenv('JIRA_URL', 'https://crometrics.atlassian.net/')
    username = os.getenv('JIRA_USERNAME', 'sean.khan@crometrics.com')
    api_token = os.getenv('JIRA_API_TOKEN')
    
    print(f"Jira URL: {jira_url}")
    print(f"Username: {username}")
    print(f"API Token: {'Set' if api_token else 'NOT SET'}")
    
    if not api_token:
        print("\n❌ CRITICAL ISSUE: JIRA_API_TOKEN is not set!")
        print("This is why the automation is failing.")
        print("\nTo fix:")
        print("1. Go to Railway dashboard")
        print("2. Add JIRA_API_TOKEN environment variable")
        print("3. Get token from: https://id.atlassian.com/manage/api-tokens")
        return False
    
    # Test basic authentication
    print(f"\n🧪 Testing authentication...")
    try:
        url = f"{jira_url.rstrip('/')}/rest/api/3/myself"
        auth = HTTPBasicAuth(username, api_token)
        headers = {'Accept': 'application/json'}
        
        response = requests.get(url, auth=auth, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Authentication successful!")
            print(f"✅ User: {user_data.get('displayName', 'Unknown')}")
            print(f"✅ Email: {user_data.get('emailAddress', 'Unknown')}")
        elif response.status_code == 401:
            print(f"❌ Authentication failed (401 Unauthorized)")
            print(f"This means the API token is invalid or expired.")
            print(f"\nTo fix:")
            print(f"1. Go to: https://id.atlassian.com/manage/api-tokens")
            print(f"2. Create a new API token")
            print(f"3. Update JIRA_API_TOKEN in Railway")
            return False
        elif response.status_code == 403:
            print(f"❌ Access forbidden (403)")
            print(f"User {username} doesn't have permission to access Jira API")
            return False
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test specific issue access
    print(f"\n🧪 Testing issue access...")
    test_issues = ['MTP-71', 'MTP-1', 'MTP-2']
    
    for issue_key in test_issues:
        try:
            url = f"{jira_url.rstrip('/')}/rest/api/3/issue/{issue_key}"
            response = requests.get(url, auth=auth, headers=headers, timeout=10)
            
            if response.status_code == 200:
                issue_data = response.json()
                print(f"✅ {issue_key}: Found - {issue_data.get('fields', {}).get('summary', 'No summary')}")
                return True
            elif response.status_code == 404:
                print(f"⚠️  {issue_key}: Not found (404)")
            else:
                print(f"❌ {issue_key}: Error {response.status_code}")
                
        except Exception as e:
            print(f"❌ {issue_key}: Error - {e}")
    
    print(f"\n❌ No accessible MTP issues found.")
    print(f"This could mean:")
    print(f"1. MTP project doesn't exist")
    print(f"2. User {username} doesn't have access to MTP project")
    print(f"3. Issue keys are different (e.g., not MTP-XX format)")
    
    return False

if __name__ == '__main__':
    diagnose_jira_api()
