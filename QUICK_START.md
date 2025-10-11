# Quick Start - Deploy to Railway Now!

Your code is now on GitHub: **https://github.com/sk-cro/qa-test-plan-automation**

## 🚀 Deploy to Railway (5 minutes)

### Step 1: Sign Up for Railway
1. Go to [railway.app](https://railway.app)
2. Click **"Login"** → Sign in with GitHub
3. Authorize Railway to access your repositories

### Step 2: Create New Project
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Search for and select: `qa-test-plan-automation`
4. Railway will start deploying automatically

### Step 3: Add Environment Variables
Click on your deployed service → **Variables** tab → Add these variables:

```bash
JIRA_API_TOKEN=your_jira_api_token_here
JIRA_URL=https://crometrics.atlassian.net/
JIRA_USERNAME=sean.khan@crometrics.com
TEMPLATE_SHEET_ID=1D8jLAB8SwxCYeBCldsIVCTHSZ9SEsMjbKvbsC5smiiU
DESTINATION_FOLDER_ID=1ZDG-Gdx9iTc-UFqje2YZtUF3vJya4MeG
LOG_LEVEL=INFO
FLASK_ENV=production
```

### Step 4: Get Your Jira API Token
1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage/api-tokens)
2. Click **"Create API token"**
3. Copy the token and add it as `JIRA_API_TOKEN` in Railway

### Step 5: Setup Google OAuth Token

**Run this locally first:**
```bash
cd "/Users/sean/Gavin QA Project"
python app.py
```

This will:
1. Open a browser for Google OAuth
2. Create `token.json` file
3. Press Ctrl+C to stop the server

**Add token to Railway:**
```bash
# Copy the entire token.json content
cat token.json

# In Railway, add a new variable:
# Name: GOOGLE_TOKEN_JSON
# Value: <paste the entire token.json content>
```

### Step 6: Get Your Railway URL
1. In Railway dashboard → Select your service
2. Go to **Settings** → **Networking**
3. Click **"Generate Domain"**
4. Copy your URL (e.g., `https://qa-test-plan-automation-production.up.railway.app`)

### Step 7: Configure Jira Webhook
1. Go to **Jira** → ⚙️ Settings → System → **WebHooks**
2. Click **"Create a WebHook"**
3. Fill in:
   - **Name**: QA Test Plan Automation
   - **Status**: ✅ Enabled
   - **URL**: `https://your-railway-app.up.railway.app/webhook`
   - **Events**: Issue → updated
   - **JQL**: (optional) `status changed to "Ready for QA"`
4. Click **"Create"**

---

## ✅ Test Your Setup

### Test 1: Health Check
```bash
curl https://your-railway-app.up.railway.app/health
```

Expected response:
```json
{"status":"healthy","service":"qa-test-plan-automation"}
```

### Test 2: Manual Test (without Jira webhook)
```bash
curl -X POST https://your-railway-app.up.railway.app/test-create \
  -H "Content-Type: application/json" \
  -d '{"issue_key":"MTP-1234"}'
```

Replace `MTP-1234` with a real Jira issue key.

### Test 3: Real Workflow
1. Go to Jira
2. Find or create a ticket
3. Move it to **"Ready for QA"** status
4. Check:
   - ✅ Railway logs show activity
   - ✅ New Google Sheet created in your folder
   - ✅ Jira comment posted with sheet URL

---

## 📊 Monitor Your App

### Railway Dashboard
- **Logs**: Click "Logs" to see real-time activity
- **Metrics**: Monitor CPU, memory, and network usage
- **Deployments**: View deployment history

### View Logs
```bash
# Check if webhook is receiving requests
# In Railway: Logs tab → Filter by "Received webhook event"
```

---

## 🔧 Troubleshooting

### App Won't Start
- Check Railway logs for errors
- Verify all environment variables are set
- Ensure `GOOGLE_TOKEN_JSON` is valid JSON

### Google Auth Fails
```bash
# Regenerate token locally:
rm token.json
python app.py
# Complete OAuth flow
# Copy new token.json to Railway
```

### Jira Webhook Not Working
- Verify Railway URL is correct in Jira webhook settings
- Check Railway logs when moving a ticket
- Test with `/test-create` endpoint first

### "Ready for QA" Not Triggering
- Verify webhook JQL filter in Jira
- Check the exact status name in Jira (case-sensitive)
- Look at webhook logs in Jira Settings → WebHooks

---

## 💰 Railway Costs

- **Hobby Plan**: $5/month
- **Usage**: ~$1-3/month for this app
- **Free Trial**: Railway offers $5 free credit

---

## 🔄 Updating Your App

```bash
cd "/Users/sean/Gavin QA Project"

# Make changes to your code
git add .
git commit -m "Your change description"
git push origin main

# Railway auto-deploys in ~2 minutes
```

---

## 📞 Need Help?

1. **Check Railway Logs**: Most issues show up here
2. **Test Manually**: Use `/test-create` endpoint
3. **Verify Environment Variables**: Double-check all are set
4. **Check Google Sheet Permissions**: Ensure OAuth token has access

---

## ✨ You're All Set!

Your QA automation is live! Every time a ticket moves to "Ready for QA", a test plan sheet will be automatically created and linked in Jira.

**GitHub**: https://github.com/sk-cro/qa-test-plan-automation
**Railway**: https://railway.app (your dashboard)

Happy automating! 🎉

