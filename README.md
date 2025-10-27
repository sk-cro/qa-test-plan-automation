# QA Test Plan Automation

A serverless Python application that automatically generates QA test plans in Google Sheets when a Jira ticket is moved to "Selected For Development" status.

## Features

- **Automated Workflow**: Triggered by Jira webhooks when tickets move to "Selected For Development"
- **Google Sheets Integration**: Creates test plan sheets from a template
- **Goals Field Parsing**: Automatically parses numbered goals from Jira "Goals" field
- **Platform Detection**: Identifies testing platform (Convert, Optimizely, or VWO) from Jira labels
- **Dynamic Content Insertion**: Inserts goals into the appropriate platform tab at row 28, column B
- **Jira Integration**: Posts comments with sheet URLs back to Jira tickets
- **Project Restrictions**: Configurable to only process issues from specific Jira projects (currently restricted to MTP project)
- **Serverless Ready**: Structured for AWS Lambda or Google Cloud Functions
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Error Handling**: Robust error handling throughout the application
- **Duplicate Prevention**: Automatically skips creating sheets for tickets that already have a test plan

## Project Structure

```
.
├── app.py                  # Main Flask application with webhook endpoint
├── config.py               # Configuration management
├── google_auth.py          # Google API authentication
├── google_sheets.py        # Google Sheets/Drive operations
├── jira_client.py          # Jira API client
├── jira_parser.py          # Jira ticket parser for platform and goals
├── sheet_customizer.py     # Google Sheet customization logic
├── serverless_aws.py       # AWS Lambda handler
├── serverless_gcp.py       # Google Cloud Functions handler
├── requirements.txt        # Python dependencies
└── .gitignore             # Git ignore patterns
```

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- Google Cloud Project with Drive and Sheets APIs enabled
- Jira account with API access
- OAuth 2.0 credentials from Google Cloud Console

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root with the following variables:

```env
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# Jira Configuration
JIRA_URL=https://crometrics.atlassian.net/
JIRA_USERNAME=sean.khan@crometrics.com
JIRA_API_TOKEN=your_jira_api_token_here

# Google Workspace Configuration
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json

# Google Sheet Template Configuration
TEMPLATE_SHEET_ID=1D8jLAB8SwxCYeBCldsIVCTHSZ9SEsMjbKvbsC5smiiU
DESTINATION_FOLDER_ID=1ZDG-Gdx9iTc-UFqje2YZtUF3vJya4MeG

# Application Settings
LOG_LEVEL=INFO

# Project Restrictions (comma-separated list of allowed Jira project keys)
ALLOWED_PROJECTS=MTP
```

### 4. Google Credentials Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable Google Drive API and Google Sheets API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the credentials JSON file and save it as `credentials.json`
6. Run the application once locally to complete the OAuth flow and generate `token.json`

### 5. Jira API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage/api-tokens)
2. Create an API token
3. Add it to your `.env` file as `JIRA_API_TOKEN`

## Running Locally

### Development Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

### Testing the Endpoint

Test the QA test plan creation without Jira webhook:

```bash
curl -X POST http://localhost:5000/test-create \
  -H "Content-Type: application/json" \
  -d '{"issue_key": "MTP-1234"}'
```

### Health Check

```bash
curl http://localhost:5000/health
```

## Deployment

### AWS Lambda

1. Package the application with dependencies:
   ```bash
   pip install -r requirements.txt -t ./package
   cp *.py ./package/
   cd package
   zip -r ../lambda_function.zip .
   cd ..
   ```

2. Create a Lambda function in AWS Console
3. Upload the `lambda_function.zip`
4. Set handler to `serverless_aws.lambda_handler`
5. Configure environment variables in Lambda settings
6. Create an API Gateway trigger

### Google Cloud Functions

1. Deploy using gcloud CLI:
   ```bash
   gcloud functions deploy qa-test-plan-automation \
     --runtime python310 \
     --trigger-http \
     --entry-point main \
     --source . \
     --set-env-vars JIRA_API_TOKEN=your_token_here
   ```

2. Configure environment variables in GCP Console
3. Note the function URL for Jira webhook configuration

## Jira Webhook Setup

1. Go to Jira Settings → System → WebHooks
2. Create a new webhook
3. Set URL to your deployed endpoint (e.g., `https://your-domain.com/webhook`)
4. Select event: "Issue → updated"
5. Configure JQL filter (optional): `status changed to "Selected For Development"`
6. Save the webhook

## Workflow

1. **Trigger**: Jira ticket status changes to "Selected For Development"
2. **Webhook**: Jira sends POST request to `/webhook` endpoint
3. **Duplicate Check**: Checks if a test plan already exists for the ticket
4. **Authentication**: Application authenticates with Google APIs
5. **Sheet Creation**: 
   - Copies template sheet
   - Renames to `{ISSUE-KEY} - QA Test Plan`
   - Moves to destination folder
6. **Content Customization**:
   - Extracts platform from Jira labels (Convert, Optimizely, or VWO)
   - Parses Goals field into numbered sections
   - Selects appropriate platform tab
   - Inserts goals starting at row 28, column B
7. **Jira Update**: Posts comment with sheet URL to Jira ticket

## API Endpoints

### `POST /webhook`
Main webhook endpoint for Jira events.

**Request**: Jira webhook payload

**Response**:
```json
{
  "issue_key": "MTP-1234",
  "sheet_url": "https://docs.google.com/spreadsheets/d/...",
  "status": "success",
  "message": "QA test plan created and Jira updated successfully"
}
```

### `POST /test-create`
Manual test endpoint (no webhook required).

**Request**:
```json
{
  "issue_key": "MTP-1234"
}
```

**Response**: Same as webhook endpoint

### `GET /health`
Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "qa-test-plan-automation"
}
```

## Error Handling

The application includes comprehensive error handling:

- **Google API Errors**: Authentication failures, permission issues, network errors
- **Jira API Errors**: Invalid credentials, issue not found, network errors
- **Validation Errors**: Missing configuration, invalid webhook payloads
- **Partial Success**: Sheet created but comment posting failed

All errors are logged with full stack traces for debugging.

## Logging

The application uses Python's built-in logging module with the following levels:

- **INFO**: Normal operations, successful API calls
- **WARNING**: Non-critical issues
- **ERROR**: API failures, exceptions
- **DEBUG**: Detailed debugging information (set `LOG_LEVEL=DEBUG`)

Logs include timestamps, module names, and log levels for easy debugging.

## Security Considerations

- **Never commit** `credentials.json`, `token.json`, or `.env` files
- Store sensitive data (API tokens) in environment variables
- Use HTTPS for all webhook endpoints
- Implement webhook signature verification for production (optional enhancement)
- Restrict Google OAuth scopes to minimum required
- Use IAM roles for serverless deployments instead of credentials files when possible

## Troubleshooting

### Google Authentication Issues
- Ensure `credentials.json` is present and valid
- Delete `token.json` and re-authenticate if credentials are stale
- Verify Drive and Sheets APIs are enabled in Google Cloud Console

### Jira Connection Issues
- Verify API token is valid and not expired
- Check Jira username and URL are correct
- Ensure Jira user has permission to comment on issues

### Webhook Not Triggering
- Verify webhook URL is publicly accessible
- Check Jira webhook configuration and JQL filter
- Review Jira webhook logs in Jira Settings

## Future Enhancements

- Additional sheet customization based on Jira ticket data
  - Metric insertion from ticket descriptions
  - Requirements extraction and insertion
  - Custom attributes handling
  - Dynamic tab hiding based on platform
- Webhook signature verification for security
- Support for multiple Jira projects/workflows
- Customizable sheet templates per project
- Slack/email notifications
- Metrics and analytics dashboard
- Automated testing suite

## License

MIT License

## Support

For issues or questions, contact: sean.khan@crometrics.com

