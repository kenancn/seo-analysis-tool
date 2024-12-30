"""
Module for running Lighthouse performance analysis using Brightdata's Scraping Browser.
"""

from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
from dotenv import load_dotenv
import streamlit as st
from typing import Tuple, Optional

# Load environment variables
load_dotenv()

def get_auth() -> str:
    """
    Retrieve Brightdata authentication credentials from environment variables or Streamlit secrets.
    
    Returns:
        str: Brightdata authentication string
        
    Note:
        Checks both .env file and Streamlit secrets for the auth token
    """
    return os.getenv("BRIGHTDATA_AUTH") or st.secrets["BRIGHTDATA_AUTH"]

# Brightdata authentication credentials
AUTH = get_auth()
SBR_WEBDRIVER = f'https://{AUTH}@brd.superproxy.io:9515'

def get_lighthouse(target_url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch Lighthouse performance metrics for both mobile and desktop versions of a webpage.
    
    Args:
        target_url (str): The URL of the webpage to analyze
        
    Returns:
        tuple: (mobile_report, desktop_report)
            - mobile_report (str): Lighthouse performance metrics for mobile
            - desktop_report (str): Lighthouse performance metrics for desktop
            
    Note:
        Uses Brightdata's Scraping Browser to access PageSpeed Insights
        Handles both mobile and desktop analysis in a single session
        Includes performance, accessibility, best practices, and SEO metrics
    """
    # Set up Brightdata Scraping Browser connection
    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, 'goog', 'chrome')
    driver = Remote(sbr_connection, options=ChromeOptions())

    try:
        # Navigate to PageSpeed Insights
        encoded_url = f"https://pagespeed.web.dev/analysis?url={target_url}"
        driver.get(encoded_url)

        # Wait for the report to load
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, "lh-report"))
        )
        time.sleep(2)
        # Get mobile report
        report_text = driver.find_element(By.TAG_NAME, "body").text
        driver.save_screenshot("lighthouse_mobile.png")
        # Switch to desktop
        desktop_tab = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "desktop_tab"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", desktop_tab)
        time.sleep(1)

        # Click desktop ta
        actions = ActionChains(driver)
        actions.move_to_element(desktop_tab).click().perform()
        time.sleep(2)

        # Wait for desktop report
        WebDriverWait(driver, 20).until(
            lambda driver: driver.find_element(By.CLASS_NAME, "lh-report").text != report_text
        )

        # Get desktop report
        desktop_report_text = driver.find_element(By.TAG_NAME, "body").text
        driver.save_screenshot("lighthouse_desktop.png")
        return report_text, desktop_report_text

    finally:
        # Close WebDriver
        driver.quit()


