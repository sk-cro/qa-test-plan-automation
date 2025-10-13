#!/usr/bin/env python3
"""
Test script to inspect the actual structure of our Google Sheet template.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google_auth import GoogleAuthManager
from config import Config

def inspect_sheet_structure():
    """Inspect the actual structure of the template sheet."""
    print("🔍 Inspecting Google Sheet Template Structure")
    print("=" * 50)
    
    try:
        # Initialize Google Sheets service
        auth_manager = GoogleAuthManager()
        sheets_service = auth_manager.get_sheets_service()
        
        # Get the template sheet
        template_id = Config.TEMPLATE_SHEET_ID
        print(f"Template Sheet ID: {template_id}")
        
        # Get sheet metadata
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=template_id,
            includeGridData=False
        ).execute()
        
        print(f"\n📊 Sheet Information:")
        print(f"Title: {spreadsheet.get('properties', {}).get('title', 'Unknown')}")
        
        sheets = spreadsheet.get('sheets', [])
        print(f"Number of sheets: {len(sheets)}")
        
        for i, sheet in enumerate(sheets):
            sheet_props = sheet.get('properties', {})
            sheet_name = sheet_props.get('title', f'Sheet {i+1}')
            sheet_id = sheet_props.get('sheetId')
            grid_props = sheet_props.get('gridProperties', {})
            
            print(f"\n📋 Sheet: {sheet_name}")
            print(f"  ID: {sheet_id}")
            print(f"  Hidden: {sheet_props.get('hidden', False)}")
            print(f"  Rows: {grid_props.get('rowCount', 'Unknown')}")
            print(f"  Columns: {grid_props.get('columnCount', 'Unknown')}")
        
        # Try to read some sample data to understand structure
        print(f"\n🔍 Sample Data from First Sheet:")
        try:
            # Read first 30 rows to understand structure
            range_name = f"{sheets[0].get('properties', {}).get('title', 'Sheet1')}!A1:Z30"
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=template_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            print(f"Found {len(values)} rows of data")
            
            # Look for specific patterns
            for i, row in enumerate(values[:20]):  # Show first 20 rows
                if row and any(cell.strip() for cell in row):  # Skip empty rows
                    row_str = ' | '.join(cell[:30] for cell in row[:5])  # First 5 columns, max 30 chars each
                    print(f"  Row {i+1}: {row_str}")
                    
                    # Look for specific keywords
                    row_text = ' '.join(row).lower()
                    if 'requirements' in row_text:
                        print(f"    ⭐ Found 'requirements' in row {i+1}")
                    if 'custom' in row_text:
                        print(f"    ⭐ Found 'custom' in row {i+1}")
                    if 'metric' in row_text:
                        print(f"    ⭐ Found 'metric' in row {i+1}")
                        
        except Exception as e:
            print(f"Error reading sheet data: {e}")
        
        print(f"\n✅ Sheet inspection completed!")
        
    except Exception as e:
        print(f"❌ Error inspecting sheet: {e}")

if __name__ == '__main__':
    inspect_sheet_structure()
