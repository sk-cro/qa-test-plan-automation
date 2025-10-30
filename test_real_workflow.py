#!/usr/bin/env python3
"""
Test the real workflow with a simulated webhook call.
"""
import requests
import json

def test_real_workflow():
    """Test the complete workflow with a simulated webhook."""
    print("🚀 Testing Real Workflow with Simulated Data")
    print("=" * 60)
    
    # Simulate a real Jira webhook payload
    webhook_payload = {
        "webhookEvent": "jira:issue_updated",
        "issue": {
            "key": "MTP-REAL-TEST",
            "fields": {
                "summary": "Real Test - Mobile CTA Optimization",
                "description": """
# Mobile CTA Button Experiment

## Primary Metric
Primary metric: Click-through Rate

## Additional Metrics
[NEW] Mobile Conversion Rate
[NEW] Time to First Click

## Requirements
- Redesign CTA button for mobile
- Change color to blue
- Increase size by 20%
- A/B test with 70/30 split

## Custom Attributes
- Device: Mobile
- Position: Centered
- Animation: Fade-in

## Internal Notes
PGM requested bounce rate tracking.
                """,
                "labels": ["mobile", "experiment", "cta"]
            }
        },
        "changelog": {
            "items": [
                {
                    "field": "status",
                    "toString": "Selected For Development"
                }
            ]
        }
    }
    
    print("📋 Simulating Jira Webhook Call")
    print("-" * 40)
    print(f"✅ Issue Key: {webhook_payload['issue']['key']}")
    print(f"✅ Status Change: {webhook_payload['changelog']['items'][0]['toString']}")
    print(f"✅ Labels: {webhook_payload['issue']['fields']['labels']}")
    
    # Test the webhook endpoint
    print("\n🌐 Calling Railway Webhook Endpoint")
    print("-" * 40)
    
    try:
        response = requests.post(
            'https://qa-test-plan-automation-production.up.railway.app/webhook',
            json=webhook_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook Response:")
            print(json.dumps(result, indent=2))
            
            if 'sheet_url' in result:
                print(f"\n🎉 SUCCESS! Sheet created: {result['sheet_url']}")
                print("📊 Check the Google Sheet to see the customized content!")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    print("\n" + "=" * 60)
    print("🧪 Test completed!")

if __name__ == '__main__':
    test_real_workflow()
