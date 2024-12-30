"""
Module for generating AI-powered SEO analysis reports using Google's Gemini AI.
Processes Lighthouse metrics and HTML content to provide comprehensive SEO recommendations.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# Get API key from environment or Streamlit secrets
def get_api_key() -> str:
    """
    Retrieve Gemini API key from environment variables or Streamlit secrets.
    
    Returns:
        str: Gemini API authentication key
        
    Note:
        Checks both .env file and Streamlit secrets for the API key
    """
    return os.getenv("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"]

# Gemini API configuration
genai.configure(api_key=get_api_key())

# Model configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

# Create model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-8b",
    generation_config=generation_config,
)

def generate_ai_report(data: dict) -> str:
    """
    Generate a comprehensive SEO analysis report using Gemini AI.
    
    Args:
        data (dict): Analysis data containing:
            - lighthouse_data (str): Lighthouse performance metrics
            - html_content (str): Webpage HTML content
            - website_url (str): Main website URL
            - article_url (str): Specific article URL
            
    Returns:
        str: Detailed SEO analysis report 
            
    Note:
        Uses Gemini AI to analyze both technical metrics and content structure
        Provides actionable insights for SEO improvement
    """
    lighthouse_data = data["lighthouse_data"] if data["lighthouse_data"] else ""
    html = data["html_content"][:3000] if data["html_content"] else ""
    website_url = data.get("website_url", "")
    article_url = data.get("article_url", "")
    
    # Start chat session
    chat_session = model.start_chat(history=[])
    
    # Send prompt
    response = chat_session.send_message(
        f"""Based on these data, generate a comprehensive SEO analysis report:
        
        Website URL: {website_url}
        Article URL: {article_url}
        
        Lighthouse Summary:
        {lighthouse_data}
        
        Homepage HTML Sample:
        {html}
        
        Please focus on:
        1. Performance metrics and their impact
        2. Accessibility issues and recommendations
        3. Best practices compliance
        4. SEO optimization opportunities
        5. Key areas for improvement
        """
    )
    
    return response.text