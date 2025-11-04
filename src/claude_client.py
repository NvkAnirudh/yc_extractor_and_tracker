import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class ClaudeClient:
    """Handles all interactions with Claude API"""

    def __init__(self, config):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key or self.api_key == 'your_anthropic_api_key_here':
            raise ValueError("Please set ANTHROPIC_API_KEY in .env file")

        self.client = Anthropic(api_key=self.api_key)
        self.model = config['claude']['model']
        self.max_tokens = config['claude']['max_tokens']
        self.temperature = config['claude']['temperature']

        # Load context (replaces resume)
        self.context_text = self._load_context()

    def _load_context(self):
        """Load context.md file"""
        context_path = 'context.md'

        if not os.path.exists(context_path):
            print(f"Warning: Context file not found at {context_path}")
            return ""

        try:
            with open(context_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: Could not read context file: {e}")
            return ""

    def extract_company_info(self, company_page_content):
        """Extract company information from company page HTML/text"""

        extraction_prompt = f"""You are a job application assistant. Extract company information from this company page content and return it as a valid JSON object:

{{
  "company_name": "string",
  "founders": [
    {{
      "name": "Founder Full Name",
      "linkedin": "Full LinkedIn URL (e.g., https://www.linkedin.com/in/username) if found, otherwise 'N/A'"
    }}
  ],
  "company_description": "Brief description of what the company does",
  "location": "Company headquarters location if mentioned",
  "industry": "Industry/sector if mentioned"
}}

CRITICAL Instructions:
- For founders: Search the ENTIRE page for founder/co-founder names and their LinkedIn profile URLs
- LinkedIn URLs might appear as:
  * Direct links: https://www.linkedin.com/in/username
  * Partial paths: /in/username (convert to full URL)
  * Text mentions: "linkedin.com/in/username"
- Look in sections like: About, Team, Founders, Leadership, or anywhere on the page
- If LinkedIn URL is not a full URL, convert it to https://www.linkedin.com/in/username format
- Extract ALL founders mentioned, not just one

Company Page Content:
{company_page_content}

Return ONLY the JSON object, no additional text."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": extraction_prompt}
                ]
            )

            response_text = message.content[0].text
            company_data = json.loads(response_text)
            return company_data

        except json.JSONDecodeError as e:
            print(f"Error parsing company info JSON: {e}")
            print(f"Raw response: {response_text}")
            return None
        except Exception as e:
            print(f"Error extracting company info: {e}")
            return None

    def extract_job_positions(self, company_page_content):
        """Extract list of job positions from company page"""

        extraction_prompt = f"""You are a job application assistant. Extract all available job positions from this company page and return them as a valid JSON array:

{{
  "positions": [
    {{
      "title": "Job Title",
      "url": "Full URL to job posting if available, otherwise 'N/A'"
    }}
  ]
}}

Instructions:
- Extract ALL job positions/openings listed on the page
- Look for sections like: "Open Positions", "Jobs", "Careers", "We're Hiring", etc.
- Each position should have a title
- If there's a link to the full job posting, include the complete URL
- If URL is relative (e.g., /jobs/123), note it as relative
- Return empty array if no positions found

Company Page Content:
{company_page_content}

Return ONLY the JSON object, no additional text."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": extraction_prompt}
                ]
            )

            response_text = message.content[0].text
            positions_data = json.loads(response_text)
            return positions_data.get('positions', [])

        except json.JSONDecodeError as e:
            print(f"Error parsing positions JSON: {e}")
            print(f"Raw response: {response_text}")
            return []
        except Exception as e:
            print(f"Error extracting positions: {e}")
            return []

    def extract_job_data(self, job_description):
        """Extract structured data from job description"""

        extraction_prompt = f"""You are a job application assistant. Extract the following information from this job description and return it as a valid JSON object:

{{
  "company_name": "string",
  "position_title": "string",
  "location": "string (e.g., 'San Francisco, CA' or 'Remote' or 'San Francisco (in-office)')",
  "employment_type": "string (e.g., 'Full-time', 'Part-time', 'Contract', 'Intern')",
  "salary_range": "string (e.g., '$120K - $180K' or 'Not specified')",
  "equity_range": "string (e.g., '0.1% - 0.5%' or 'Not specified')",
  "founders": [
    {{
      "name": "Founder Name",
      "linkedin": "LinkedIn URL if available, otherwise 'N/A'"
    }}
  ],
  "required_experience": "string (e.g., '3-5 years' or 'Senior level' or extract key experience requirements)",
  "visa_sponsorship": "string ('Yes', 'No', or 'Not specified')"
}}

Important extraction guidelines:
- For founders: CAREFULLY extract founder/CEO/Co-founder names from the job description. Look for sections like "About the Company", "Team", "About Us", author information, or any mentions of founders. Also extract their LinkedIn profiles if mentioned (look for linkedin.com URLs). If no founders mentioned, return empty array []
- For employment_type: Infer from context if not explicitly stated (default to 'Full-time' for most positions)
- For visa_sponsorship: Look for phrases like "visa sponsorship available", "must be authorized to work", "US work authorization required", etc.
- For location: Include any work arrangement details (remote, hybrid, in-office)
- For required_experience: Summarize years of experience or seniority level required

CRITICAL: Search the ENTIRE job description thoroughly for founder names and LinkedIn URLs. They may appear anywhere in the text.

Job Description:
{job_description}

Return ONLY the JSON object, no additional text."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.3,  # Lower temperature for extraction
                messages=[
                    {"role": "user", "content": extraction_prompt}
                ]
            )

            response_text = message.content[0].text
            # Parse JSON from response
            extracted_data = json.loads(response_text)
            return extracted_data

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Raw response: {response_text}")
            return None
        except Exception as e:
            print(f"Error extracting job data: {e}")
            return None

    def generate_personalized_message(self, job_description, extracted_data):
        """Generate a personalized application message based on context and job description

        Uses prompt caching for the context to reduce costs and improve performance.
        """

        if not self.context_text:
            return "Context file not available. Please add context.md to generate personalized message."

        # Get founder information for salutation
        founders_list = extracted_data.get('founders', [])
        founder_name = "Hiring Team"
        if founders_list and len(founders_list) > 0:
            founder_name = founders_list[0].get('name', 'Hiring Team')

        # Message prompt without context (will be added separately for caching)
        message_prompt = f"""You are a professional job application assistant. Generate a compelling, personalized application message for the following job based on the candidate's background and experience.

Job Information:
Company: {extracted_data.get('company_name', 'N/A')}
Position: {extracted_data.get('position_title', 'N/A')}
Location: {extracted_data.get('location', 'N/A')}
Employment Type: {extracted_data.get('employment_type', 'Full-time')}
Salary Range: {extracted_data.get('salary_range', 'Not specified')}
Required Experience: {extracted_data.get('required_experience', 'Not specified')}
Founder/Contact Name: {founder_name}

Job Description:
{job_description}

STRICT Requirements:
1. START with a salutation addressing {founder_name} (e.g., "Hi {founder_name}," or "Hello {founder_name},")
2. Keep the ENTIRE message under 500 characters (including the salutation)
3. Be extremely concise - highlight only 1-2 most relevant experiences/skills
4. Show enthusiasm for the role
5. Match the company tone (startup = casual, enterprise = formal)
6. End with interest in discussing further
7. NO formal closing or signature needed

Generate ONLY the application message text, ready to copy and paste. Keep it under 500 characters total."""

        try:
            # Use prompt caching for the context (which rarely changes)
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=[
                    {
                        "type": "text",
                        "text": "You are a professional job application assistant helping candidates write compelling, personalized application messages."
                    },
                    {
                        "type": "text",
                        "text": f"Here is the candidate's complete professional profile and background:\n\n{self.context_text}",
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[
                    {"role": "user", "content": message_prompt}
                ]
            )

            personalized_message = message.content[0].text
            return personalized_message.strip()

        except Exception as e:
            print(f"Error generating personalized message: {e}")
            return "Error generating message"
