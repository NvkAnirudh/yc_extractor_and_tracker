# YC Extractor and Job Application Tracker

An automated job application tracker that scrapes Y Combinator's "Work at a Startup" company pages, extracts job postings, and generates personalized application messages using Claude AI.

## Features

- 🔍 **Company Page Scraping**: Automatically scrapes YC company pages using Selenium
- 👥 **Founder Information**: Extracts founder names and LinkedIn profiles
- 💼 **Job Listings**: Displays all available positions with interactive selection
- 🤖 **AI-Powered Messages**: Generates personalized 500-character application messages using Claude
- 📊 **Google Sheets Integration**: Automatically saves all data to Google Sheets
- 🔄 **Continuous Processing**: Process multiple companies in one session
- ✅ **Duplicate Detection**: Prevents duplicate job entries

## Project Structure

```
yc_scraper/
├── src/                          # Core modules
│   ├── __init__.py
│   ├── claude_client.py          # Claude API integration
│   └── sheets_manager.py         # Google Sheets management
├── config/                       # Configuration files
│   ├── config.json               # Application settings
│   └── .env.example              # Environment variables template
├── examples/                     # Example files
│   ├── context.example.md        # Template for personal context
│   └── credentials.example.json  # Google credentials template
├── docs/                         # Documentation
│   └── OLD_README.md            # Legacy documentation
├── claude_job_extractor.py       # Main application script
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## Prerequisites

- Python 3.10+
- Google Cloud Project with Sheets API enabled
- Anthropic API key (Claude)
- Chrome/Chromium browser (for Selenium)

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd yc_extractor_and_tracker
```

### 2. Create virtual environment

```bash
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
uv pip install -r requirements.txt
```

### 4. Set up Google Sheets

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API and Google Drive API
4. Create a Service Account
5. Download credentials JSON file
6. Save it as `credentials.json` in the project root
7. Create a Google Sheet named "Job_Application_Tracker"
8. Share the sheet with your service account email (found in credentials.json)

### 5. Set up environment variables

```bash
cp config/.env.example .env
```

Edit `.env` with your values:

```env
# Anthropic API Key
ANTHROPIC_API_KEY=your_api_key_here

# Google Sheets Configuration
GOOGLE_SHEET_NAME=Job_Application_Tracker
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/your-sheet-id/edit
GOOGLE_CREDENTIALS_FILE=credentials.json
```

### 6. Create your context file

```bash
cp examples/context.example.md context.md
```

Edit `context.md` with your professional background, skills, and experience.

## Usage

### Interactive Mode (Recommended)

```bash
python claude_job_extractor.py
```

The script will:
1. Prompt for a YC company page URL
2. Scrape and display all available positions
3. Let you select a position
4. Generate a personalized message
5. Save everything to Google Sheets
6. Ask if you want to process another company

### Command-Line Mode

```bash
python claude_job_extractor.py --url https://www.workatastartup.com/companies/company-name
```

### Example

```bash
$ python claude_job_extractor.py

================================================================================
JOB APPLICATION TRACKER V2
================================================================================

Enter the company page URL (or 'quit' to exit):
Example: https://www.workatastartup.com/companies/reform

URL: https://www.workatastartup.com/companies/reform

📥 Fetching company page: https://www.workatastartup.com/companies/reform

⏳ Extracting company information... ✓
   Company: Reform
   Founders: Omar Abuhashish, Pradhit Gosula

⏳ Extracting available positions... ✓ (5 positions found)

================================================================================
AVAILABLE POSITIONS AT REFORM
================================================================================

1. Technical Recruiter
2. Product Manager
3. Senior Software Engineer
4. Forward Deployed Engineer
5. Enterprise Account Executive

6. Cancel

Select a position (1-6): 3

✓ Selected: Senior Software Engineer

⏳ Extracting job details... ✓
⏳ Generating personalized message... ✓
⏳ Updating Google Sheets... ✓

================================================================================
PERSONALIZED APPLICATION MESSAGE
================================================================================

Hi Omar Abuhashish,

[Your personalized message here]

================================================================================
✓ Message saved to Google Sheets!
📊 Character count: 455/500
================================================================================

Process another company? (y/n):
```

## Google Sheets Output

The script creates a spreadsheet with the following columns:

| Column | Description |
|--------|-------------|
| Company Name | Name of the company |
| Position Title | Job title |
| Location | Job location |
| Employment Type | Full-time, Part-time, etc. |
| Job Description Link | URL to job posting |
| Salary Range | Salary information |
| Equity Range | Equity information |
| Founder 1 | First founder's name |
| Founder 1 LinkedIn | First founder's LinkedIn URL |
| Founder 2 | Second founder's name |
| Founder 2 LinkedIn | Second founder's LinkedIn URL |
| Required Experience | Experience requirements |
| Visa Sponsorship | Visa sponsorship availability |
| Match % | Manual field for your notes |
| Personalized Message | AI-generated message |
| Application Date | Date added to tracker |
| Status | Application status |

## Configuration

### config/config.json

```json
{
  "claude": {
    "model": "claude-3-5-haiku-20241022",
    "max_tokens": 4096,
    "temperature": 0.7
  },
  "sheets": {
    "columns": [...],
    "default_status": "Not Applied"
  }
}
```

### Message Generation

Messages are:
- **Limited to 500 characters** including salutation
- **Personalized** based on your context.md
- **Address founders by name** when available
- **Highlight relevant experience** matching the job

## Cost Estimates

Using Claude Haiku (cost-effective):
- Company info extraction: ~$0.002-0.005 per company
- Job data extraction: ~$0.002-0.005 per job
- Message generation: ~$0.002-0.005 per message (with caching)

**Total: ~$0.006-0.015 per job application**

With prompt caching, the context.md is cached for 5 minutes, making subsequent requests 70-80% cheaper.

## Features in Detail

### Duplicate Detection
Automatically checks if a job already exists in your tracker (by company name + position title) and skips if found.

### Founder LinkedIn Extraction
Scrapes LinkedIn URLs from company pages and stores them separately for easy access.

### Interactive Position Selection
Instead of processing all positions, you choose which one interests you.

### Continuous Processing
Process multiple companies without restarting the script or re-initializing APIs.

## Troubleshooting

### Chrome Driver Issues
```bash
# The script uses webdriver-manager to auto-install ChromeDriver
# If issues persist, manually install Chrome or Chromium
```

### Google Sheets Permission Denied
- Ensure the sheet is shared with your service account email
- Check that both Sheets API and Drive API are enabled
- Use the full spreadsheet URL in GOOGLE_SHEET_URL

### Context Not Loading
- Ensure `context.md` exists in the project root
- Check file permissions
- Verify the file is not empty

### API Rate Limits
- Claude API has rate limits based on your plan
- Add delays between requests if needed
- Use Haiku model for cost efficiency

## Development

### Running Tests
```bash
# No automated tests yet - contributions welcome!
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Security Notes

⚠️ **Never commit these files:**
- `.env` - Contains API keys
- `credentials.json` - Google service account credentials
- `context.md` - Your personal resume/background

All these files are in `.gitignore` by default.

## License

[Add your license here]

## Acknowledgments

- Built with [Anthropic Claude API](https://www.anthropic.com/)
- Uses [gspread](https://github.com/burnash/gspread) for Google Sheets
- Web scraping with [Selenium](https://www.selenium.dev/)

## Support

For issues or questions:
1. Check the [docs](docs/) folder
2. Review existing issues
3. Open a new issue with details

---

**Happy Job Hunting! 🚀**
