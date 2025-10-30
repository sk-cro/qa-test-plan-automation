# Deployment Guide - GitHub & Railway

This guide will walk you through deploying the QA Test Plan Automation application to Railway via GitHub.

## Prerequisites

- [GitHub Account](https://github.com)
- [Railway Account](https://railway.app) (sign up with GitHub)
- Git installed on your local machine
- Jira API Token
- Google OAuth 2.0 credentials (`credentials.json`)

---

## Part 1: Push to GitHub

### Step 1: Initialize Git Repository

```bash
cd "/Users/sean/Gavin QA Project"
git init
git add .
git commit -m "Initial commit: QA Test Plan Automation"
```

### Step 2: Create GitHub Repository

**Option A: Using GitHub CLI (if installed)**
```bash
gh repo create qa-test-plan-automation --public --source=. --remote=origin
git push -u origin main
```

**Option B: Using GitHub Web Interface**

1. Go to [GitHub](https://github.com/new)
2. Repository name: `qa-test-plan-automation`
3. Choose **Public** or **Private**
4. Do NOT initialize with README (we already have one)
5. Click "Create repository"
6. Copy the repository URL and run:

```bash
git remote add origin https://github.com/YOUR_USERNAME/qa-test-plan-automation.git
git branch -M main
git push -u origin main
```

---

## Part 2: Deploy to Railway

### Step 1: Sign Up for Railway

1. Go to [railway.app](https://railway.app)
2. Click "Login" and sign in with GitHub
3. Authorize Railway to access your repositories

### Step 2: Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose `qa-test-plan-automation` repository
4. Railway will automatically detect it's a Python app

### Step 3: Configure Environment Variables

In Railway dashboard, go to your project → Variables tab and add:

```
JIRA_API_TOKEN=your_jira_api_token_here
JIRA_URL=https://crometrics.atlassian.net/
JIRA_USERNAME=sean.khan@crometrics.com
TEMPLATE_SHEET_ID=1D8jLAB8SwxCYeBCldsIVCTHSZ9SEsMjbKvbsC5smiiU
DESTINATION_FOLDER_ID=1ZDG-Gdx9iTc-UFqje2YZtUF3vJya4MeG
LOG_LEVEL=INFO
FLASK_ENV=production
FLASK_DEBUG=False
```

### Step 4: Handle Google Credentials

**Important**: Railway needs the Google credentials. You have two options:

#### Option A: Use Service Account (Recommended for Production)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a Service Account
3. Download the JSON key
4. Add it as an environment variable in Railway:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
   ```
5. Convert the JSON to base64 and add:
   ```
   GOOGLE_CREDENTIALS_BASE64=<base64_encoded_json>
   ```
6. You'll need to modify the code slightly to decode this (see below)

#### Option B: Use OAuth with Pre-generated Token (Quick Start)

1. Run locally first to generate `token.json`
2. Add the content as environment variables in Railway:
   ```
   GOOGLE_TOKEN_JSON=<paste_entire_token.json_content>
   ```
3. Modify `google_auth.py` to read from env var

### Step 5: Deploy

1. Railway will automatically deploy after you add environment variables
2. Monitor the deployment logs in Railway dashboard
3. Once deployed, note your Railway URL (e.g., `https://your-app.up.railway.app`)

---

## Part 3: Configure Jira Webhook

### Step 1: Get Your Railway URL

In Railway dashboard, find your deployed service URL (Settings → Domains)

### Step 2: Set Up Jira Webhook

1. Go to Jira Settings → System → WebHooks
2. Click "Create a WebHook"
3. Name: `QA Test Plan Automation`
4. Status: **Enabled**
5. URL: `https://your-app.up.railway.app/webhook`
6. Events to trigger:
   - Issue → updated
7. JQL Filter (optional): `status changed to "Selected For Development"`
8. Click "Create"

### Step 3: Test the Integration

1. Move a Jira ticket to "Selected For Development" status
2. Check Railway logs for activity
3. Verify Google Sheet was created
4. Check Jira ticket for comment with sheet URL

---

## Part 4: Testing Before Going Live

### Test Using the Manual Endpoint

```bash
curl -X POST https://your-app.up.railway.app/test-create \
  -H "Content-Type: application/json" \
  -d '{"issue_key": "MTP-1234"}'
```

### Health Check

```bash
curl https://your-app.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "qa-test-plan-automation"
}
```

---

## Handling Google OAuth on Railway

Since Railway is a headless environment, you need to handle OAuth differently:

### Option 1: Pre-generate Token Locally (Easiest)

1. Run app locally first
2. Complete OAuth flow
3. Copy `token.json` content
4. Store as Railway environment variable

Add this to `google_auth.py`:

```python
import os
import json

# In the authenticate() method, before checking if token_file exists:
if os.getenv('GOOGLE_TOKEN_JSON'):
    logger.info("Loading credentials from environment variable")
    token_data = json.loads(os.getenv('GOOGLE_TOKEN_JSON'))
    self.credentials = Credentials.from_authorized_user_info(token_data, self.scopes)
    if self.credentials and self.credentials.valid:
        return self.credentials
```

### Option 2: Use Service Account (Better for Production)

1. Create a Service Account in Google Cloud Console
2. Share the template sheet with the service account email
3. Share the destination folder with the service account email
4. Use service account credentials instead of OAuth

---

## Troubleshooting

### Deployment Fails

- Check Railway logs for specific errors
- Verify all environment variables are set
- Ensure `requirements.txt` includes all dependencies

### Google Authentication Issues

- Verify credentials are properly set in environment
- Check token hasn't expired
- Ensure service account has access to template and folder

### Jira Webhook Not Working

- Verify webhook URL is correct and publicly accessible
- Check Railway logs when triggering from Jira
- Verify Jira API token is valid
- Check webhook configuration in Jira

### Railway App Crashes

- Check Railway logs for Python errors
- Verify PORT environment variable is being used correctly
- Ensure all required environment variables are set

---

## Monitoring

### Railway Dashboard

- View real-time logs
- Monitor CPU and memory usage
- Track deployment history
- Check build logs

### Set Up Alerts (Optional)

Consider adding monitoring services:
- [Sentry](https://sentry.io) for error tracking
- [Better Stack](https://betterstack.com) for uptime monitoring
- [Papertrail](https://papertrailapp.com) for log management

---

## Cost Considerations

Railway offers:
- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage

This app should run well on the Hobby plan.

---

## Security Best Practices

✅ Never commit `credentials.json`, `token.json`, or `.env` files
✅ Use Railway's environment variables for all secrets
✅ Enable webhook signature verification (optional enhancement)
✅ Use HTTPS for all endpoints (Railway provides this automatically)
✅ Regularly rotate API tokens
✅ Monitor Railway logs for suspicious activity

---

## Updating the Application

```bash
# Make changes to your code
git add .
git commit -m "Your commit message"
git push origin main
```

Railway will automatically detect the push and redeploy.

---

## Support

For issues:
- Check Railway logs first
- Review Jira webhook logs
- Test with `/test-create` endpoint
- Contact: sean.khan@crometrics.com

