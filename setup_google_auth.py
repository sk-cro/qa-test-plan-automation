#!/usr/bin/env python3
"""
Setup script to help configure Google OAuth authentication.
This script will guide you through getting the Google credentials.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Google API scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

def main():
    print("🔧 Google OAuth Setup for QA Test Plan Automation")
    print("=" * 50)
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("\n❌ credentials.json not found!")
        print("\n📋 To get credentials.json:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Google Drive API and Google Sheets API")
        print("4. Go to: Credentials → Create Credentials → OAuth 2.0 Client IDs")
        print("5. Application type: Desktop application")
        print("6. Download the JSON file and save as 'credentials.json'")
        print("\n⚠️  Once you have credentials.json, run this script again.")
        return
    
    print("✅ credentials.json found!")
    
    # Check if token already exists
    if os.path.exists('token.json'):
        print("✅ token.json already exists!")
        
        # Load existing token
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if creds and creds.valid:
            print("✅ Valid credentials found! No setup needed.")
            show_token_for_railway()
            return
        elif creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
                print("✅ Credentials refreshed!")
                show_token_for_railway()
                return
            except Exception as e:
                print(f"❌ Failed to refresh credentials: {e}")
                print("🔄 Starting new OAuth flow...")
    
    # Start OAuth flow
    print("\n🚀 Starting Google OAuth flow...")
    print("This will open your browser for authentication.")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        print("✅ Authentication successful!")
        print("✅ token.json created!")
        
        show_token_for_railway()
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\n💡 Troubleshooting:")
        print("- Make sure credentials.json is valid")
        print("- Check your internet connection")
        print("- Ensure you have access to the Google account")

def show_token_for_railway():
    """Display the token content for Railway deployment."""
    print("\n" + "=" * 50)
    print("🚀 READY FOR RAILWAY DEPLOYMENT!")
    print("=" * 50)
    
    # Read token file
    with open('token.json', 'r') as f:
        token_content = f.read()
    
    print("\n📋 Copy this ENTIRE content and add it to Railway:")
    print("Variable name: GOOGLE_TOKEN_JSON")
    print("Variable value:")
    print("-" * 30)
    print(token_content)
    print("-" * 30)
    
    print("\n📝 Railway Environment Variables to add:")
    print("JIRA_API_TOKEN=your_jira_api_token_here")
    print("JIRA_URL=https://crometrics.atlassian.net/")
    print("JIRA_USERNAME=sean.khan@crometrics.com")
    print("TEMPLATE_SHEET_ID=1D8jLAB8SwxCYeBCldsIVCTHSZ9SEsMjbKvbsC5smiiU")
    print("DESTINATION_FOLDER_ID=1ZDG-Gdx9iTc-UFqje2YZtUF3vJya4MeG")
    print("GOOGLE_TOKEN_JSON=<paste_the_content_above>")
    print("LOG_LEVEL=INFO")
    print("FLASK_ENV=production")
    
    print("\n🎉 You're ready to deploy to Railway!")

if __name__ == '__main__':
    main()
