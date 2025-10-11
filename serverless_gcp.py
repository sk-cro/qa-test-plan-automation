"""
Google Cloud Functions handler for the QA Test Plan automation.

This module provides the Cloud Function entry point for GCP deployment.
"""
import json
import logging
from flask import Flask, request

from app import jira_webhook, health_check, test_create, initialize_app

# Configure logging for GCP Cloud Functions
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the app once at cold start
try:
    initialize_app()
except Exception as e:
    logger.error(f"Failed to initialize app: {e}")


def main(request):
    """
    Google Cloud Function HTTP entry point.
    
    Args:
        request (flask.Request): The request object.
        
    Returns:
        Response: Flask response object.
    """
    try:
        # Route based on path
        path = request.path
        method = request.method
        
        logger.info(f"Cloud Function invoked: {method} {path}")
        
        if path == '/health' and method == 'GET':
            return health_check()
        elif path == '/webhook' and method == 'POST':
            return jira_webhook()
        elif path == '/test-create' and method == 'POST':
            return test_create()
        else:
            return {'error': 'Not found'}, 404
            
    except Exception as e:
        logger.error(f"Cloud Function error: {e}", exc_info=True)
        return {'error': 'Internal server error'}, 500

