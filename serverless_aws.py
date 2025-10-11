"""
AWS Lambda handler for the QA Test Plan automation.

This module provides the Lambda function entry point for AWS deployment.
"""
import json
import logging
from app import handler as app_handler

# Configure logging for AWS Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event (dict): Lambda event data containing the HTTP request.
        context: Lambda context object.
        
    Returns:
        dict: Response with statusCode, body, and headers.
    """
    logger.info(f"Lambda invoked with event: {json.dumps(event)}")
    
    try:
        response = app_handler(event, context)
        return response
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }

