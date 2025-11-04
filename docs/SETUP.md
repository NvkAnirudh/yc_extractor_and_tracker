# Detailed Setup Guide

This guide provides step-by-step instructions for setting up the YC Job Application Tracker.

## Table of Contents
1. [Google Cloud Setup](#google-cloud-setup)
2. [Anthropic API Setup](#anthropic-api-setup)
3. [Application Configuration](#application-configuration)
4. [Creating Your Context](#creating-your-context)
5. [Testing the Setup](#testing-the-setup)

---

## Google Cloud Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Enter a project name (e.g., "YC Job Tracker")
4. Click **Create**

### Step 2: Enable Required APIs

1. In your project, go to **APIs & Services** → **Library**
2. Search for and enable:
   - **Google Sheets API**
   - **Google Drive API**

### Step 3: Create Service Account

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Enter service account details:
   - Name: `yc-job-tracker`
   - Description: "Service account for job application tracker"
4. Click **Create and Continue**
5. Skip role assignment (click **Continue**)
6. Click **Done**

### Step 4: Download Credentials

1. Find your service account in the list
2. Click on it to open details
3. Go to the **Keys** tab
4. Click **Add Key** → **Create new key**
5. Choose **JSON** format
6. Click **Create**
7. Save the downloaded file as `credentials.json` in your project root

### Step 5: Set Up Google Sheet

1. Create a new Google Sheet at [sheets.google.com](https://sheets.google.com)
2. Name it: `Job_Application_Tracker`
3. Copy the sheet URL (will look like: `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`)
4. Click **Share** button
5. Add your service account email (found in `credentials.json` as `client_email`)
6. Give it **Editor** permissions
7. Click **Send**

**Important**: Leave the sheet empty - headers will be created automatically.

---

## Anthropic API Setup

### Step 1: Create Anthropic Account

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to **API Keys**

### Step 2: Generate API Key

1. Click **Create Key**
2. Name it (e.g., "YC Job Tracker")
3. Copy the API key immediately (shown only once!)
4. Store it safely

### Step 3: Add Credits (if needed)

1. Go to **Billing** section
2. Add payment method
3. Purchase credits or set up auto-recharge

**Cost**: With Haiku model, expect ~$0.01 per job application.

---

## Application Configuration

### Step 1: Clone and Install

```bash
git clone <your-repo>
cd yc_extractor_and_tracker

# Create virtual environment
uv venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Copy example
cp config/.env.example .env

# Edit with your values
nano .env  # or use your preferred editor
```

Your `.env` should look like:

```env
# Anthropic API Key (required)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Sheets Configuration
GOOGLE_SHEET_NAME=Job_Application_Tracker
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
GOOGLE_CREDENTIALS_FILE=credentials.json
```

**Where to find values:**
- `ANTHROPIC_API_KEY`: From Anthropic console
- `GOOGLE_SHEET_URL`: From your Google Sheet's address bar
- `GOOGLE_CREDENTIALS_FILE`: Path to your credentials JSON (default: `credentials.json` in project root)

### Step 3: Place Credentials File

```bash
# Copy your downloaded credentials to project root
cp ~/Downloads/your-project-xxxxx.json credentials.json
```

---

## Creating Your Context

### Step 1: Create context.md

```bash
# Copy the example
cp examples/context.example.md context.md

# Edit with your information
nano context.md
```

### Step 2: Fill Out Your Information

Include:
- **Professional summary**: 2-3 sentences about your background
- **Contact information**: Email, LinkedIn, GitHub, portfolio
- **Education**: Degrees, certifications, relevant coursework
- **Work experience**: Companies, roles, achievements, technologies
- **Technical skills**: Languages, frameworks, tools, databases
- **Key projects**: Personal or professional projects with impact
- **Measurable achievements**: Numbers that demonstrate your impact

### Step 3: Writing Tips

✅ **Do:**
- Be specific and quantitative ("Improved performance by 40%")
- Highlight relevant technologies
- Include links to GitHub/portfolio
- Keep it concise but informative
- Update regularly

❌ **Don't:**
- Use generic buzzwords without specifics
- Include sensitive information
- Make it too long (2-3 pages max)
- Forget to update after new experiences

### Example Snippet

```markdown
## Professional Experience

### Nidhi AI - Founding Engineer (Jan 2024 - Present)
- Built production Text2SQL platform using GPT-4, FastAPI, and React
- Reduced query processing time by 60% through caching layer
- Implemented multi-tenant PostgreSQL architecture serving 50+ clients
- Technologies: Python, FastAPI, React, PostgreSQL, Redis, Docker

### eContenti - Data Engineer (Jan 2023 - Dec 2023)
- Developed ETL pipelines processing 2M+ records daily
- Reduced query execution time by 35% through optimization
- Generated $200K in productivity savings through automation
- Technologies: Python, Apache Airflow, Snowflake, dbt
```

---

## Testing the Setup

### Step 1: Test Google Sheets Connection

Create a test script `test_sheets.py`:

```python
from src.sheets_manager import SheetsManager
import json

with open('config/config.json') as f:
    config = json.load(f)

sheets = SheetsManager(config)
info = sheets.get_sheet_info()
print(f"✓ Connected! Sheet has {info['total_rows']} rows")
```

Run it:
```bash
python test_sheets.py
```

### Step 2: Test Claude API

Create a test script `test_claude.py`:

```python
from src.claude_client import ClaudeClient
import json

with open('config/config.json') as f:
    config = json.load(f)

claude = ClaudeClient(config)
print("✓ Claude API initialized successfully!")
print(f"Using model: {claude.model}")
```

Run it:
```bash
python test_claude.py
```

### Step 3: Run Full Test

```bash
# Test with a real company
python claude_job_extractor.py --url https://www.workatastartup.com/companies/reform
```

Expected output:
1. Company information extracted
2. Positions displayed
3. Prompts for position selection
4. Generates personalized message
5. Saves to Google Sheets

---

## Troubleshooting

### Error: "Spreadsheet not found"

**Solution:**
1. Verify sheet is shared with service account email
2. Check `GOOGLE_SHEET_URL` in `.env` is correct
3. Ensure both Sheets API and Drive API are enabled

### Error: "Invalid API key"

**Solution:**
1. Check `ANTHROPIC_API_KEY` in `.env`
2. Ensure no extra spaces or quotes
3. Verify key is active in Anthropic console

### Error: "Context file not found"

**Solution:**
1. Create `context.md` in project root: `cp examples/context.example.md context.md`
2. Fill it with your information
3. Check file permissions

### Error: "ChromeDriver not found"

**Solution:**
1. The script auto-installs ChromeDriver via `webdriver-manager`
2. Ensure Chrome/Chromium is installed
3. Check internet connection for driver download

### Error: "Permission denied" on credentials.json

**Solution:**
```bash
chmod 600 credentials.json
```

### Google Sheets shows "insufficient permissions"

**Solution:**
1. Delete existing credentials: `rm credentials.json`
2. Create new service account key
3. Re-share sheet with new service account email

---

## Next Steps

Once setup is complete:

1. **Test with one company** to verify everything works
2. **Review the generated message** to ensure quality
3. **Adjust your context.md** if messages need improvement
4. **Start tracking applications!**

For usage instructions, see the main [README.md](../README.md).

---

## Getting Help

If you encounter issues:

1. Check this guide thoroughly
2. Review error messages carefully
3. Verify all API keys and URLs
4. Check file permissions
5. Look for typos in configuration files

Still stuck? Open an issue with:
- Error message
- Steps you've tried
- Your environment (OS, Python version)
