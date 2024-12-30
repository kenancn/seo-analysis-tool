"""
Module for competitor analysis and content comparison.
Provides functionality to:
- Fetch competitor URLs from search results
- Compare article content with competitors
- Analyze SEO strategies and patterns
- Generate detailed comparison reports
"""

import json
from bs4 import BeautifulSoup
import requests
import os
import google.generativeai as genai
import urllib.request
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# Get API keys from environment or Streamlit secrets
def get_api_key(key_name):
    return os.getenv(key_name) or st.secrets[key_name]

# Gemini API configuration
genai.configure(api_key=get_api_key("GEMINI_API_KEY"))

# Gemini model configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-8b",
    generation_config=generation_config,
)

def fetch_html_content(url: str) -> tuple:
    """
    Fetch and parse HTML content from a given URL using Brightdata API.
    
    Args:
        url (str): The target URL to fetch content from
        
    Returns:
        tuple: (url, html_content)
            - url (str): The processed URL
            - html_content (str): Parsed HTML content or None if failed
            
    Note:
        Extracts main content tags (h1, h2, h3, p) for analysis
    """
    # Ensure the URL has a proper scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        # Brightdata API configuration
        api_url = "https://api.brightdata.com/request"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_api_key('BRIGHTDATA_API_KEY')}"
        }
        payload = {
            "zone": "web_unlocker1",
            "url": url,
            "format": "raw"
        }
        
        # Make request to Brightdata API
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            tags = soup.find_all(['h1', 'h2', 'h3', 'p'])
            collected_html = ''.join(str(tag) for tag in tags)
            return url, collected_html
        else:
            print(f"Error from Brightdata API: {response.status_code}")
            return url, None

    except Exception as e:
        print(f"Error fetching HTML content from {url}: {e}")
        return url, None



def get_top_competitor(keyword: str, our_domain: str) -> str:
    """
    Retrieve the top-ranking competitor URL for a given keyword, excluding our domain.
    
    Args:
        keyword (str): The target keyword to search for
        our_domain (str): Our website's domain to exclude from results
        
    Returns:
        str: URL of the top-ranking competitor, or None if not found
        
    Note:
        Uses Brightdata SERP API to fetch real-time search results
    """
    try:
        url = "https://api.brightdata.com/request"
        
        # URL encode the keyword
        encoded_keyword = requests.utils.quote(keyword)
        
        payload = {
            "zone": "serp_api1",
            "url": f"https://www.google.com/search?q={encoded_keyword}",
            "format": "raw"
        }
        
        headers = {
            "Authorization": f"Bearer {get_api_key('BRIGHTDATA_API_KEY')}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all search results
            all_data = soup.find_all("div", {"class": "g"})
            position = 0
            search_results = []
            
            for result in all_data:
                try:
                    link_element = result.find('a')
                    if not link_element:
                        continue
                        
                    link = link_element.get('href')
                    
                    # Validate link format
                    if (link and 
                        link.find('https') != -1 and 
                        link.find('http') == 0 and 
                        link.find('aclk') == -1):
                        
                        position += 1
                        result_data = {
                            "link": link,
                            "position": position
                        }
                        
                        # Get title
                        try:
                            result_data["title"] = result.find('h3', {"class": "DKV0Md"}).text
                        except:
                            result_data["title"] = None
                            
                        # Get description    
                        try:
                            result_data["description"] = result.find("div", {"class": "VwiC3b"}).text
                        except:
                            result_data["description"] = None
                            
                        search_results.append(result_data)
                except Exception as e:
                    print(f"Error parsing result: {e}")
                    continue
            
            # Return first result URL that's not our domain
            for result in search_results:
                if our_domain not in result["link"]:
                    return result["link"]
    
        return None
    except Exception as e:
        print(f"Error in getting competitor: {e}")
        return None

def fetch_page_content(url: str) -> str:
    """
    Fetch and parse webpage content focusing on main article content.
    
    Args:
        url (str): The target URL to fetch content from
        
    Returns:
        str: Extracted main content text or None if failed
        
    Note:
        Prioritizes content within main, article, or content-specific div tags
    """
    try:
        # Brightdata API configuration
        api_url = "https://api.brightdata.com/request"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_api_key('BRIGHTDATA_API_KEY')}"
        }
        payload = {
            "zone": "web_unlocker1",
            "url": url,
            "format": "raw"
        }
        
        # Make request to Brightdata API
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            main_content = soup.find_all(['main', 'article', 'div'], class_=['content', 'main', 'body'])
            
            if not main_content:
                main_content = soup.find_all(['h1', 'h2', 'h3', 'p'])
                
            return ' '.join([tag.get_text(strip=True) for tag in main_content])
        
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def compare_articles(our_url: str, competitor_url: str, main_keyword: str) -> str:
    """
    Perform comprehensive SEO comparison between two articles.
    
    Args:
        our_url (str): URL of our article
        competitor_url (str): URL of competitor's article
        main_keyword (str): Primary keyword for comparison
        
    Returns:
        str: Detailed SEO analysis report
        
    Note:
        Focuses on content structure, relevance, and optimization patterns
    """
    try:
        # Extract domain from our URL
        our_domain = our_url.split('/')[2] if '//' in our_url else our_url.split('/')[0]
        
        if not competitor_url:
            return "Could not find competitor URL"
        
        our_content = fetch_page_content(our_url)
        competitor_content = fetch_page_content(competitor_url)
        
        if not our_content or not competitor_content:
            return "Error fetching page content"
            
        # Professional SEO analysis prompt
        prompt = f"""Conduct a comprehensive SEO content analysis comparing two articles:

        Target Keyword: {main_keyword}

        Analysis Focus:
        - Content structure and organization
        - Semantic relevance and topic coverage
        - User engagement potential
        - Content optimization patterns

        Compare Article 1 (Reference) with Article 2 (Competitor) based on content quality metrics:
        Article 1: {our_content}
        Article 2: {competitor_content}

        Provide insights on:
        1. Structural advantages/disadvantages
        2. Content depth and comprehensiveness
        3. User experience and readability
        4. SEO optimization patterns
        5. Strategic recommendations"""
        
        # Send message to Gemini
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(prompt)
        
        return response.text
        
    except Exception as e:
        print(f"Error in article comparison: {e}")
        return None

# result= compare_articles("https://www.geeksforgeeks.org","Web Scraping")
# print(result)
