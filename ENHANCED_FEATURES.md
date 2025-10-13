# Enhanced QA Test Plan Automation Features

## 🚀 What's New

The automation now handles **ALL** the detailed QA test plan customization steps from your process:

### ✅ **Complete Automation Workflow**

1. **✅ Template Management**
   - Copies master template sheet
   - Renames to `{ISSUE-KEY} - QA Test Plan`
   - Moves to QA folder

2. **✅ Platform Detection**
   - Reads experiment platform from Jira labels
   - Hides non-relevant experiment tabs
   - Keeps only: `hidden`, `{Platform} QA Pass1`, `Complexity & Risk`

3. **✅ Custom Attributes Handling**
   - Detects if ticket has custom attributes
   - If **0 custom attributes**: Deletes rows 17, 30, 31, 54, 55
   - If **has custom attributes**: Adds them to Custom Attribute section

4. **✅ Metrics Management**
   - Extracts primary metric from ticket description
   - Finds `[NEW]` prefixed metrics
   - Inserts primary metric into all Metrics sections
   - Adds `[NEW]` metrics to appropriate sections
   - Creates additional rows if more than 2 metrics

5. **✅ Requirements Processing**
   - Extracts experiment requirements from ticket description
   - Inserts formatted requirements into "Spec Requirements" section
   - Expands section with additional rows if content is too long

6. **✅ Dynamic Content Insertion**
   - Parses ticket labels, custom fields, and description
   - Handles multiple platforms (Web, Mobile, Backend, Email, etc.)
   - Supports future enhancement for internal notes

## 📊 **Enhanced Data Extraction**

### From Jira Tickets:
- **Platform**: Detected from labels (Web, Mobile, Backend, Email, Push, SMS)
- **Primary Metric**: Extracted from description or first `[NEW]` metric
- **Additional Metrics**: All `[NEW]` prefixed metrics
- **Custom Attributes**: From description and custom fields
- **Requirements**: Formatted experiment requirements
- **Internal Notes**: Ready for future implementation

### Smart Parsing:
- Regex-based extraction for structured data
- Fallback defaults when data is missing
- Error handling for malformed content
- Length limits to prevent sheet overflow

## 🔧 **Technical Implementation**

### New Modules:
- **`jira_parser.py`**: Extracts and processes ticket data
- **`sheet_customizer.py`**: Handles dynamic sheet customization
- **Enhanced `app.py`**: Orchestrates the complete workflow

### Google Sheets API Operations:
- Sheet metadata retrieval
- Tab management (hide/show/delete)
- Dynamic row insertion/deletion
- Content insertion with formatting
- Batch operations for efficiency

## 🎯 **Supported Platforms**

The automation detects these platforms from Jira labels:
- **Web** (default)
- **Mobile** (iOS, Android, App)
- **Backend** (API, Server)
- **Email** (Mail)
- **Push** (Notification)
- **SMS** (Text)

## 📝 **Ticket Format Support**

### Labels for Platform Detection:
- `web`, `website`, `frontend` → Web
- `mobile`, `ios`, `android`, `app` → Mobile
- `backend`, `api`, `server` → Backend
- `email`, `mail` → Email
- `push`, `notification` → Push
- `sms`, `text` → SMS

### Metrics Detection:
- Primary: `primary metric:`, `main metric:`, `primary KPI:`
- Additional: `[NEW] metric_name`
- Auto-detection from description text

### Custom Attributes:
- `custom attribute:`, `additional attribute:`, `custom field:`
- Any custom field values from Jira

### Requirements:
- `requirements:`, `experiment requirements:`, `changes:`, `specification:`
- Falls back to first paragraph if no specific section

## 🔄 **Workflow Example**

1. **Jira Ticket**: `MTP-1234` with labels `[web, experiment]` and description:
   ```
   Primary metric: Click-through Rate
   [NEW] Conversion Rate
   [NEW] Time on Page
   
   Requirements:
   - Add new CTA button
   - Change button color to blue
   - Update mobile layout
   ```

2. **Automation Creates**:
   - Sheet named: `MTP-1234 - QA Test Plan`
   - Hides non-Web platform tabs
   - Deletes custom attribute rows (no custom attributes detected)
   - Inserts "Click-through Rate" as primary metric
   - Adds "[NEW] Conversion Rate" and "[NEW] Time on Page"
   - Inserts requirements into Spec Requirements section
   - Posts comment to Jira with sheet URL

## 🚀 **Ready for Production**

The enhanced automation is now deployed and ready to handle your complete QA test plan process automatically!

### Test with Real Tickets:
```bash
curl -X POST https://qa-test-plan-automation-production.up.railway.app/test-create \
  -H "Content-Type: application/json" \
  -d '{"issue_key":"MTP-1234"}'
```

### Expected Response:
```json
{
  "issue_key": "MTP-1234",
  "sheet_url": "https://docs.google.com/spreadsheets/d/...",
  "status": "success",
  "message": "Enhanced QA test plan created and Jira updated successfully",
  "customization_success": true,
  "ticket_data": {
    "platform": "Web",
    "primary_metric": "Click-through Rate",
    "has_custom_attributes": false
  }
}
```

## 🔮 **Future Enhancements Ready**

The system is architected to easily support:
- Internal notes processing
- Additional metric verification from PGM requests
- Custom template variations per project
- Advanced formatting and styling
- Multi-language support

Your QA automation is now **production-ready** with full customization support! 🎉
