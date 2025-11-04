#!/usr/bin/env python3
"""
Claude Job Extractor V2
Enhanced version with company page scraping and position selection
"""

import sys
import json
import os
import argparse
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from src.claude_client import ClaudeClient
from src.sheets_manager import SheetsManager


def load_config():
    """Load configuration from config.json"""
    with open('config/config.json', 'r') as f:
        return json.load(f)


def fetch_page(url):
    """Fetch web page with JavaScript rendering using Selenium"""
    driver = None
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

        # Initialize driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Load page
        driver.get(url)

        # Wait for page to load (wait for body to be present)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Additional wait for dynamic content
        time.sleep(3)

        # Get page source
        page_source = driver.page_source

        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract LinkedIn URLs before removing elements
        linkedin_links = []
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if 'linkedin.com/in/' in href.lower():
                # Normalize URL
                if not href.startswith('http'):
                    href = 'https://' + href.lstrip('/')
                linkedin_links.append(href)

        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'header', 'footer']):
            script.decompose()

        # Get text
        text = soup.get_text(separator='\n', strip=True)

        # Clean up text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        clean_text = '\n'.join(lines)

        # Append LinkedIn URLs to the content so Claude can see them
        if linkedin_links:
            clean_text += '\n\n--- LinkedIn Profiles Found ---\n'
            clean_text += '\n'.join(linkedin_links)

        return clean_text

    except Exception as e:
        print(f"Error fetching URL: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def build_full_url(base_url, relative_url):
    """Build full URL from base and relative URL"""
    if relative_url.startswith('http'):
        return relative_url
    return urljoin(base_url, relative_url)


def display_position_menu(positions, company_name):
    """Display interactive menu for position selection"""
    print("\n" + "="*80)
    print(f"AVAILABLE POSITIONS AT {company_name.upper()}")
    print("="*80 + "\n")

    if not positions:
        print("No positions found on this company page.")
        return None

    for i, pos in enumerate(positions, 1):
        print(f"{i}. {pos['title']}")

    print(f"\n{len(positions) + 1}. Cancel")
    print()

    while True:
        try:
            choice = input(f"Select a position (1-{len(positions) + 1}): ").strip()
            choice_num = int(choice)

            if choice_num == len(positions) + 1:
                print("Cancelled.")
                return None

            if 1 <= choice_num <= len(positions):
                return positions[choice_num - 1]
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(positions) + 1}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nCancelled.")
            return None


def merge_company_and_job_data(company_info, job_data):
    """Merge company information with job-specific data"""
    merged = job_data.copy() if job_data else {}

    # Company info takes precedence for these fields
    if company_info:
        merged['company_name'] = company_info.get('company_name', merged.get('company_name', 'N/A'))

        # Use founders from company page (more reliable)
        if company_info.get('founders'):
            merged['founders'] = company_info['founders']

        # Use company location if job doesn't specify
        if not merged.get('location') or merged.get('location') == 'N/A':
            merged['location'] = company_info.get('location', 'Not specified')

    return merged


def process_company_page(company_url, claude_client, sheets_manager):
    """Main workflow for company page processing"""

    print("\n" + "="*80)
    print("JOB APPLICATION TRACKER V2")
    print("="*80)
    print(f"\n📥 Fetching company page: {company_url}\n")

    # Step 1: Fetch company page
    company_page_content = fetch_page(company_url)
    if not company_page_content:
        print("Error: Could not fetch company page")
        return False

    # Step 2: Extract company information
    print("⏳ Extracting company information...", end='', flush=True)
    company_info = claude_client.extract_company_info(company_page_content)
    if not company_info:
        print(" ✗")
        print("Error: Could not extract company information")
        return False
    print(" ✓")

    company_name = company_info.get('company_name', 'Unknown Company')
    print(f"   Company: {company_name}")

    founders = company_info.get('founders', [])
    if founders:
        print(f"   Founders: {', '.join([f['name'] for f in founders])}")

    # Step 3: Extract job positions
    print("\n⏳ Extracting available positions...", end='', flush=True)
    positions = claude_client.extract_job_positions(company_page_content)
    if not positions:
        print(" ✗")
        print("Error: No positions found on company page")
        return False
    print(f" ✓ ({len(positions)} positions found)")

    # Step 4: Display menu and get user selection
    selected_position = display_position_menu(positions, company_name)
    if not selected_position:
        return False

    print(f"\n✓ Selected: {selected_position['title']}\n")

    # Step 5: Fetch selected job posting
    job_url = selected_position.get('url', 'N/A')

    # If URL is relative or N/A, try to construct it or use company page
    if job_url == 'N/A' or not job_url.startswith('http'):
        print(f"⚠️  No direct job URL found. Using company page content for job details.")
        job_description = company_page_content  # Use company page as fallback
        job_url = company_url
    else:
        # Build full URL if needed
        job_url = build_full_url(company_url, job_url)
        print(f"📥 Fetching job posting: {job_url}\n")
        job_description = fetch_page(job_url)

        if not job_description:
            print("⚠️  Could not fetch job posting. Using company page content.")
            job_description = company_page_content
            job_url = company_url

    # Step 6: Extract job-specific data
    print("⏳ Extracting job details...", end='', flush=True)
    job_data = claude_client.extract_job_data(job_description)
    if not job_data:
        print(" ✗")
        print("Error: Could not extract job data")
        return False
    print(" ✓")

    # Step 7: Merge company and job data
    final_data = merge_company_and_job_data(company_info, job_data)

    # Ensure we have the selected position title
    final_data['position_title'] = selected_position['title']

    # Step 8: Generate personalized message
    print("⏳ Generating personalized message...", end='', flush=True)
    personalized_message = claude_client.generate_personalized_message(job_description, final_data)
    print(" ✓")

    # Step 9: Save to Google Sheets
    print("⏳ Updating Google Sheets...", end='', flush=True)
    success = sheets_manager.append_job(final_data, job_url, personalized_message)
    if not success:
        print(" ✗")
        return False
    print(" ✓\n")

    # Step 10: Display result
    char_count = len(personalized_message)
    print("="*80)
    print("PERSONALIZED APPLICATION MESSAGE")
    print("="*80 + "\n")
    print(personalized_message)
    print("\n" + "="*80)
    print(f"✓ Message saved to Google Sheets!")
    print(f"📊 Character count: {char_count}/500")
    print("="*80 + "\n")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Extract job info from company pages and save to Google Sheets'
    )
    parser.add_argument(
        '--url',
        type=str,
        help='Company page URL (e.g., https://www.workatastartup.com/companies/reform)'
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    # Initialize clients once
    try:
        claude_client = ClaudeClient(config)
        sheets_manager = SheetsManager(config)
    except Exception as e:
        print(f"Error initializing: {e}")
        sys.exit(1)

    # Main loop for processing multiple URLs
    first_run = True
    company_url = args.url  # Use command-line URL on first run if provided

    while True:
        # Get company URL
        if not company_url:
            # Interactive mode
            if first_run:
                print("\n" + "="*80)
                print("JOB APPLICATION TRACKER V2")
                print("="*80)

            print("\nEnter the company page URL (or 'quit' to exit):")
            print("Example: https://www.workatastartup.com/companies/reform")
            company_url = input("\nURL: ").strip()

            if not company_url or company_url.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Exiting. Thank you!")
                break

        # Process company page
        success = process_company_page(company_url, claude_client, sheets_manager)

        if not success:
            print("⚠️  Could not process company page. Try another URL.\n")

        # Ask if user wants to process another URL
        print("\n" + "="*80)
        try:
            continue_choice = input("Process another company? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                print("\n👋 Exiting. Thank you!")
                break
        except KeyboardInterrupt:
            print("\n\n👋 Exiting. Thank you!")
            break

        # Reset for next iteration
        company_url = None
        first_run = False


if __name__ == '__main__':
    main()
