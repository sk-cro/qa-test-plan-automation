"""
Main Flask application for QA Test Plan automation.
Listens for Jira webhook events and creates Google Sheets accordingly.
"""
import logging
import sys
from flask import Flask, request, jsonify

from config import Config
from google_sheets import GoogleSheetsManager
from jira_client import JiraClient
from jira_parser import JiraTicketParser
from sheet_customizer import SheetCustomizer

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize service managers
sheets_manager = GoogleSheetsManager()
jira_client = JiraClient()
ticket_parser = JiraTicketParser()
sheet_customizer = SheetCustomizer()


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        Response: JSON response indicating service health.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'qa-test-plan-automation'
    }), 200


@app.route('/webhook', methods=['POST'])
def jira_webhook():
    """
    Main webhook endpoint for Jira events.
    
    Triggered when a Jira ticket is moved to "Ready for QA" status.
    Creates a QA test plan Google Sheet and posts a comment back to Jira.
    
    Returns:
        Response: JSON response with operation status.
    """
    try:
        # Parse webhook payload
        payload = request.get_json()
        
        if not payload:
            logger.warning("Received webhook with no payload")
            return jsonify({'error': 'No payload received'}), 400
        
        logger.info(f"Received webhook event: {payload.get('webhookEvent', 'unknown')}")
        
        # Check if this is a status change event
        webhook_event = payload.get('webhookEvent', '')
        
        if webhook_event != 'jira:issue_updated':
            logger.info(f"Ignoring non-update event: {webhook_event}")
            return jsonify({'message': 'Event type not relevant'}), 200
        
        # Extract issue information
        issue = payload.get('issue', {})
        issue_key = issue.get('key')
        
        if not issue_key:
            logger.error("No issue key found in webhook payload")
            return jsonify({'error': 'No issue key found'}), 400
        
        # Check if status changed to "Ready for QA"
        changelog = payload.get('changelog', {})
        items = changelog.get('items', [])
        
        status_changed_to_qa = False
        for item in items:
            if item.get('field') == 'status' and item.get('toString', '').lower() == 'ready for qa':
                status_changed_to_qa = True
                break
        
        if not status_changed_to_qa:
            logger.info(f"Issue {issue_key} status not changed to 'Ready for QA', ignoring")
            return jsonify({'message': 'Status not changed to Ready for QA'}), 200
        
        logger.info(f"Processing issue {issue_key} - Status changed to 'Ready for QA'")
        
        # Create QA test plan
        result = create_qa_test_plan(issue_key)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def create_qa_test_plan(issue_key):
    """
    Create a comprehensive QA test plan for a Jira issue.
    
    This function orchestrates the enhanced workflow:
    1. Parse Jira ticket data (platform, metrics, requirements, etc.)
    2. Create a copy of the template sheet
    3. Rename it with the Jira issue key
    4. Move it to the destination folder
    5. Customize the sheet content based on ticket data
    6. Post a comment to Jira with the sheet URL
    
    Args:
        issue_key (str): The Jira issue key (e.g., "MTP-1234").
        
    Returns:
        dict: Result containing issue_key, sheet_url, and status.
        
    Raises:
        Exception: If any step fails.
    """
    try:
        logger.info(f"Starting enhanced QA test plan creation for {issue_key}")
        
        # Step 1: Parse Jira ticket data (with fallback)
        logger.info(f"Parsing ticket data for {issue_key}")
        try:
            ticket_data = ticket_parser.parse_ticket_for_qa_plan(issue_key)
        except Exception as e:
            logger.warning(f"Failed to parse ticket {issue_key} from Jira: {e}")
            logger.info("Creating basic sheet without customization")
            # Create basic ticket data for fallback
            ticket_data = {
                'issue_key': issue_key,
                'platform': 'Web',  # Default platform
                'primary_metric': None,
                'additional_metrics': [],
                'custom_attributes': [],
                'requirements': f'QA Test Plan for {issue_key}',
                'has_custom_attributes': False,
                'internal_notes': ''
            }
        
        # Step 2-4: Create the basic Google Sheet
        sheet_info = sheets_manager.create_qa_test_plan(issue_key)
        sheet_id = sheet_info['sheet_id']
        sheet_url = sheet_info['sheet_url']
        
        logger.info(f"Basic QA test plan created: {sheet_url}")
        
        # Step 5: Customize the sheet based on ticket data (with fallback)
        logger.info(f"Customizing sheet with ticket data")
        customization_success = False
        try:
            customization_success = sheet_customizer.customize_qa_test_plan(sheet_id, ticket_data)
            if customization_success:
                logger.info(f"Sheet customization completed successfully for {issue_key}")
            else:
                logger.warning(f"Sheet customization failed for {issue_key}, but basic sheet was created")
        except Exception as e:
            logger.warning(f"Sheet customization failed for {issue_key}: {e}")
            logger.info("Basic sheet created without customization")
        
        # Step 6: Post comment to Jira
        try:
            jira_client.post_qa_plan_comment(issue_key, sheet_url)
            logger.info(f"Comment posted to Jira issue {issue_key}")
        except Exception as e:
            # Log error but don't fail the entire operation
            # The sheet was created successfully
            logger.error(f"Failed to post comment to Jira: {e}")
            return {
                'issue_key': issue_key,
                'sheet_url': sheet_url,
                'status': 'partial_success',
                'message': 'Sheet created and customized but failed to post comment to Jira',
                'error': str(e),
                'customization_success': customization_success
            }
        
        return {
            'issue_key': issue_key,
            'sheet_url': sheet_url,
            'status': 'success',
            'message': 'Enhanced QA test plan created and Jira updated successfully',
            'customization_success': customization_success,
            'ticket_data': {
                'platform': ticket_data['platform'],
                'primary_metric': ticket_data['primary_metric'],
                'has_custom_attributes': ticket_data['has_custom_attributes']
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create enhanced QA test plan: {e}")
        raise


@app.route('/test-create', methods=['POST'])
def test_create():
    """
    Test endpoint to manually trigger QA test plan creation.
    
    Expects JSON payload with 'issue_key' field.
    Useful for testing without setting up Jira webhooks.
    
    Returns:
        Response: JSON response with operation result.
    """
    try:
        data = request.get_json()
        
        if not data or 'issue_key' not in data:
            return jsonify({'error': 'issue_key is required'}), 400
        
        issue_key = data['issue_key']
        logger.info(f"Test endpoint called for issue: {issue_key}")
        
        result = create_qa_test_plan(issue_key)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def initialize_app():
    """
    Initialize the application by validating configuration and services.
    """
    try:
        logger.info("Initializing application...")
        
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize Google services (authenticate)
        sheets_manager.initialize_services()
        logger.info("Google services initialized successfully")
        
        logger.info("Application initialization complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise


# For serverless environments (AWS Lambda, Google Cloud Functions)
def handler(event, context):
    """
    Serverless handler function for AWS Lambda or similar platforms.
    
    Args:
        event (dict): Event data from the serverless platform.
        context: Runtime context.
        
    Returns:
        dict: Response with statusCode and body.
    """
    try:
        # Initialize app on first invocation
        initialize_app()
        
        # Parse event based on platform
        # This is a simplified example - actual implementation depends on platform
        if 'body' in event:
            import json
            payload = json.loads(event['body'])
            
            # Simulate Flask request
            with app.test_request_context(
                path='/webhook',
                method='POST',
                json=payload
            ):
                response = jira_webhook()
                
                return {
                    'statusCode': response[1],
                    'body': response[0].get_data(as_text=True),
                    'headers': {
                        'Content-Type': 'application/json'
                    }
                }
        
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid event format'})
        }
        
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


if __name__ == '__main__':
    # Initialize the application
    initialize_app()
    
    # Run the Flask development server
    port = 5000
    logger.info(f"Starting Flask server on port {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=Config.FLASK_DEBUG
    )

