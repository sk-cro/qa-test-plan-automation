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


def _qa_plan_already_exists(issue_key):
    """
    Check if a QA test plan comment already exists for this issue.
    
    Args:
        issue_key (str): The Jira issue key (e.g., "MTP-1234").
        
    Returns:
        bool: True if QA test plan already exists, False otherwise.
    """
    try:
        logger.info(f"Checking if QA test plan already exists for {issue_key}")
        
        # Get issue details to check existing comments
        issue_data = jira_client.get_issue(issue_key)
        comments = issue_data.get('fields', {}).get('comment', {}).get('comments', [])
        
        # Check if any comment contains "QA Test Plan has been created"
        for comment in comments:
            comment_body = comment.get('body', {})
            if isinstance(comment_body, dict):
                # Extract text from comment body (Jira uses structured content)
                comment_text = _extract_text_from_jira_body(comment_body)
            else:
                comment_text = str(comment_body)
            
            if "QA Test Plan has been created:" in comment_text:
                logger.info(f"Found existing QA test plan comment for {issue_key}")
                return True
        
        logger.info(f"No existing QA test plan found for {issue_key}")
        return False
        
    except Exception as e:
        logger.error(f"Error checking for existing QA test plan: {e}")
        # If we can't check, assume it doesn't exist to avoid blocking legitimate requests
        return False


def _extract_text_from_jira_body(body):
    """
    Extract plain text from Jira's structured comment body.
    
    Args:
        body (dict): Jira comment body structure.
        
    Returns:
        str: Plain text content.
    """
    if not isinstance(body, dict):
        return str(body)
    
    text_parts = []
    
    # Handle Jira's document structure
    content = body.get('content', [])
    for item in content:
        if item.get('type') == 'paragraph':
            for content_item in item.get('content', []):
                if content_item.get('type') == 'text':
                    text_parts.append(content_item.get('text', ''))
    
    return ' '.join(text_parts)


def is_project_allowed(issue_key):
    """
    Check if the issue's project is in the allowed projects list.
    
    Args:
        issue_key (str): The Jira issue key (e.g., "MTP-1234").
        
    Returns:
        bool: True if the project is allowed, False otherwise.
    """
    if not issue_key:
        return False
    
    # Extract project key from issue key (e.g., "MTP" from "MTP-1234")
    project_key = issue_key.split('-')[0] if '-' in issue_key else issue_key
    
    # If ALLOWED_PROJECTS is empty or contains empty string, allow all projects
    allowed_projects = [p.strip() for p in Config.ALLOWED_PROJECTS if p.strip()]
    
    if not allowed_projects:
        return True
    
    return project_key in allowed_projects


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
        
        # Check if the project is allowed
        if not is_project_allowed(issue_key):
            project_key = issue_key.split('-')[0] if '-' in issue_key else issue_key
            logger.info(f"Ignoring issue {issue_key} from project {project_key} (not in allowed projects: {Config.ALLOWED_PROJECTS})")
            return jsonify({
                'message': f'Project {project_key} is not in the allowed projects list',
                'allowed_projects': Config.ALLOWED_PROJECTS
            }), 200
        
        # Check if status changed to "Ready for QA"
        changelog = payload.get('changelog', {})
        items = changelog.get('items', [])
        
        status_changed_to_qa = False
        for item in items:
            if item.get('field') == 'status':
                from_status = item.get('fromString', '').strip()
                to_status = item.get('toString', '').strip()
                
                # Check if this is actually a status change TO "Ready for QA"
                # and NOT from "Ready for QA" (to prevent loops)
                if (to_status.lower() == 'ready for qa' and 
                    from_status.lower() != 'ready for qa'):
                    status_changed_to_qa = True
                    logger.info(f"Status change detected: '{from_status}' → '{to_status}'")
                    break
        
        if not status_changed_to_qa:
            logger.info(f"Issue {issue_key} - No valid status change to 'Ready for QA' detected, ignoring")
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
    Create a QA test plan for a Jira issue with Goals field customization.
    
    This function orchestrates the workflow:
    1. Create a copy of the template sheet
    2. Rename it with the Jira issue key
    3. Move it to the destination folder
    4. Parse Goals field and platform from Jira
    5. Insert goals into the appropriate platform tab at row 28
    6. Post a comment to Jira with the sheet URL
    
    Args:
        issue_key (str): The Jira issue key (e.g., "MTP-1234").
        
    Returns:
        dict: Result containing issue_key, sheet_url, and status.
        
    Raises:
        Exception: If any step fails.
    """
    try:
        logger.info(f"Starting QA test plan creation for {issue_key}")
        
        # Check if QA test plan already exists for this issue
        if _qa_plan_already_exists(issue_key):
            logger.info(f"QA test plan already exists for {issue_key}, skipping creation")
            return {
                'issue_key': issue_key,
                'status': 'skipped',
                'message': 'QA test plan already exists for this issue'
            }
        
        # Create the Google Sheet
        sheet_info = sheets_manager.create_qa_test_plan(issue_key)
        sheet_id = sheet_info['sheet_id']
        sheet_url = sheet_info['sheet_url']
        
        logger.info(f"QA test plan created: {sheet_url}")
        
        # Parse platform and goals from Jira
        platform = ticket_parser.extract_platform_from_labels(issue_key)
        goals = ticket_parser.parse_goals_field(issue_key)
        
        logger.info(f"Platform detected: {platform}")
        logger.info(f"Goals found: {len(goals)}")
        
        # Customize the sheet with goals if any exist
        if goals:
            try:
                logger.info(f"Starting sheet customization with {len(goals)} goals for platform {platform}")
                sheet_customizer.customize_sheet_with_goals(sheet_id, platform, goals)
                logger.info(f"Successfully customized sheet with {len(goals)} goals in {platform}")
            except Exception as e:
                logger.error(f"Failed to customize sheet with goals: {e}", exc_info=True)
                # Continue anyway - sheet was created successfully
        else:
            # Post warning to Jira if no goals found
            try:
                warning_message = "Warning: No Goals field found in ticket. Sheet created without goals."
                jira_client.add_comment(issue_key, warning_message)
                logger.info(f"Warning posted to Jira for {issue_key}")
            except Exception as comment_error:
                logger.error(f"Failed to post warning to Jira: {comment_error}")
        
        # Post comment to Jira
        try:
            jira_client.post_qa_plan_comment(issue_key, sheet_url)
            logger.info(f"Comment posted to Jira issue {issue_key}")
        except Exception as e:
            # Log error but don't fail the entire operation
            # The sheet was created successfully
            logger.error(f"Failed to post comment to Jira: {e}")
            # Try to post error notification to Jira
            try:
                error_message = f"❌ QA Test Plan automation failed: {str(e)}"
                jira_client.add_comment(issue_key, error_message)
                logger.info(f"Error notification posted to Jira for {issue_key}")
            except Exception as comment_error:
                logger.error(f"Failed to post error notification to Jira: {comment_error}")
            
            return {
                'issue_key': issue_key,
                'sheet_url': sheet_url,
                'status': 'partial_success',
                'message': 'Sheet created but failed to post comment to Jira',
                'error': str(e)
            }
        
        return {
            'issue_key': issue_key,
            'sheet_url': sheet_url,
            'status': 'success',
            'message': 'QA test plan created and Jira updated successfully',
            'platform': platform,
            'goals_inserted': len(goals) if goals else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to create QA test plan: {e}")
        
        # Try to post error notification to Jira
        try:
            error_message = f"❌ QA Test Plan automation failed: {str(e)}"
            jira_client.add_comment(issue_key, error_message)
            logger.info(f"Error notification posted to Jira for {issue_key}")
        except Exception as comment_error:
            logger.error(f"Failed to post error notification to Jira: {comment_error}")
        
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
        
        # Check if the project is allowed
        if not is_project_allowed(issue_key):
            project_key = issue_key.split('-')[0] if '-' in issue_key else issue_key
            logger.warning(f"Rejecting test request for issue {issue_key} from project {project_key} (not in allowed projects: {Config.ALLOWED_PROJECTS})")
            return jsonify({
                'error': f'Project {project_key} is not in the allowed projects list',
                'allowed_projects': Config.ALLOWED_PROJECTS
            }), 403
        
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

