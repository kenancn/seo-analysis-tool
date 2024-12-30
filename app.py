"""
Main application module for SEO Performance Analysis Tool.

This module provides a Streamlit-based web interface for:
- Analyzing website performance using Google Lighthouse
- Comparing content with top competitors
- Generating AI-powered SEO recommendations
- Visualizing performance metrics
- Exporting detailed analysis reports

The application combines multiple APIs and services to provide
comprehensive SEO analysis and actionable insights.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from typing import Dict, Optional, Tuple

from utilities.compare_pages import (
    fetch_html_content,
    compare_articles,
    get_top_competitor,
)
from utilities.lightHTMLsum import generate_ai_report
from utilities.lighthouse import get_lighthouse


# Constants
PAGE_TITLE = "SEO Performance Analysis Tool"
PAGE_ICON = "📊"
LAYOUT = "wide"

# Tab names
TAB_LIGHTHOUSE = "📊 Lighthouse Results"
TAB_CONTENT = "📝 Content Analysis"
TAB_COMPETITOR = "🔄 Competitor Analysis"

# CSS styles
CUSTOM_CSS = """
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
"""

# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)

# Apply custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def extract_homepage_url(article_url: str) -> str:
    """
    Extract the homepage URL from a given article URL.
    
    Args:
        article_url (str): The full article URL to process
        
    Returns:
        str: The extracted homepage URL (domain with protocol)
        
    Example:
        >>> extract_homepage_url("https://example.com/article/123")
        "https://example.com"
        
    """
    if not article_url:
        raise ValueError("Article URL cannot be empty")
        
    parts = article_url.split('/')
    if '//' in article_url:
        return f"{parts[0]}//{parts[2]}"
    return parts[0]

def extract_metrics(text: str) -> Dict[str, float]:
    """
    Extract Lighthouse performance metrics from the analysis text.
    
    Args:
        text (str): Raw Lighthouse analysis text containing performance scores
        
    Returns:
        Dict[str, float]: Dictionary containing performance metrics
            
    Note:
        All scores are converted from percentage (0-100) to decimal (0.0-1.0)
    """
    if not text:
        st.error("Analysis text is empty")
        return {}
        
    metrics: Dict[str, float] = {}
    
    # Patterns for metrics
    patterns = {
        'Performance': r'(\d+)\nPerformance',
        'Accessibility': r'(\d+)\nAccessibility',
        'Best Practices': r'(\d+)\nBest Practices',
        'SEO': r'(\d+)\nSEO'
    }
    
    try:
        for metric, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                score = int(match.group(1))
                metrics[metric] = score / 100
            else:
                metrics[metric] = 0.0  # Default value if metric not found
        
        return metrics
        
    except Exception as e:
        st.error(f"Error extracting metrics: {str(e)}")
        return {
            'Performance': 0.0,
            'Accessibility': 0.0,
            'Best Practices': 0.0,
            'SEO': 0.0
        }

# Header
st.title("🚀 SEO Performance Analysis Tool")
st.markdown("---")

# Input fields
col1, col2 = st.columns(2)
with col1:
    article_url = st.text_input("Article URL", placeholder="https://example.com/article")
with col2:
    keyword = st.text_input("Keyword", placeholder="Enter your main keyword")

# Analysis button
if st.button("Start Analysis", type="primary"):
    if article_url and keyword:
        with st.spinner("Analysis in progress... This may take a few minutes."):
            try:
                # Get competitor URL
                competitor_url = get_top_competitor(keyword, article_url.split('/')[2])
                
                # Create tabs for different sections using constants
                tab1, tab2, tab3 = st.tabs([TAB_LIGHTHOUSE, TAB_CONTENT, TAB_COMPETITOR])
                homepage_url = extract_homepage_url(article_url)
                
                with tab1:
                    st.subheader("Lighthouse Performance Metrics")
                    mobile_report, desktop_report = get_lighthouse(homepage_url)
                    
                    if mobile_report and desktop_report:
                        # Parse metrics for display
                        mobile_data = extract_metrics(mobile_report)
                        desktop_data = extract_metrics(desktop_report)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### 📱 Mobile Results")
                            for metric, value in mobile_data.items():
                                st.metric(
                                    label=metric,
                                    value=f"{int(value * 100)}%"
                                )
                        
                        with col2:
                            st.markdown("### 🖥️ Desktop Results")
                            for metric, value in desktop_data.items():
                                st.metric(
                                    label=metric,
                                    value=f"{int(value * 100)}%"
                                )
                            
                        # Prepare metrics for radar chart
                        metrics = list(mobile_data.keys())
                        mobile_values = [mobile_data[m] * 100 for m in metrics]
                        desktop_values = [desktop_data[m] * 100 for m in metrics]
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(
                            r=mobile_values,
                            theta=metrics,
                            fill='toself',
                            name='Mobile',
                            line=dict(color='#FF1E1E', width=2),
                            fillcolor='rgba(255, 30, 30, 0.4)'
                        ))
                        fig.add_trace(go.Scatterpolar(
                            r=desktop_values,
                            theta=metrics,
                            fill='toself',
                            name='Desktop',
                            line=dict(color='#00B4D8', width=2),
                            fillcolor='rgba(0, 180, 216, 0.4)'
                        ))
                        
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 100]
                                ),
                                bgcolor='rgba(255, 255, 255, 0.9)'
                            ),
                            showlegend=True,
                            title="Mobile vs Desktop Performance Comparison",
                            paper_bgcolor='rgba(255, 255, 255, 0)',
                            plot_bgcolor='rgba(255, 255, 255, 0)'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    st.subheader("Page Content Analysis")
                    _, html_content = fetch_html_content(article_url)
                    if html_content:
                        # Use original texts for AI report
                        combined_data = {
                            'lighthouse_data': f"MOBILE REPORT:\n{mobile_report[:3000]}\n\nDESKTOP REPORT:\n{desktop_report[:3000]}",
                            'html_content': html_content,
                            'website_url': homepage_url,
                            'article_url': article_url
                        }
                        ai_report = generate_ai_report(combined_data)
                        st.markdown(ai_report)
                
                with tab3:
                    st.subheader("Competitor Analysis")
                    if competitor_url:
                        st.markdown(f"**🎯 Top Ranking Competitor URL:** {competitor_url}")
                        comparison_result = compare_articles(article_url, competitor_url, keyword)
                        st.markdown("### 📊 Comparison Results")
                        st.markdown(comparison_result)
                    else:
                        st.warning("No competitor URL found.")
                
                # Export results
                results_data = {
                    'Basic Information': {
                        'Article URL': article_url,
                        'Keyword': keyword,
                        'Competitor URL': competitor_url
                    },
                    'Mobile Metrics': mobile_data,
                    'Desktop Metrics': desktop_data
                }
                
                # Flatten the nested dictionary for CSV
                flattened_data = {
                    'Article URL': results_data['Basic Information']['Article URL'],
                    'Keyword': results_data['Basic Information']['Keyword'],
                    'Competitor URL': results_data['Basic Information']['Competitor URL'],
                    'Mobile Performance': f"{int(results_data['Mobile Metrics'].get('Performance', 0) * 100)}%",
                    'Mobile Accessibility': f"{int(results_data['Mobile Metrics'].get('Accessibility', 0) * 100)}%",
                    'Mobile Best Practices': f"{int(results_data['Mobile Metrics'].get('Best Practices', 0) * 100)}%",
                    'Mobile SEO': f"{int(results_data['Mobile Metrics'].get('SEO', 0) * 100)}%",
                    'Desktop Performance': f"{int(results_data['Desktop Metrics'].get('Performance', 0) * 100)}%",
                    'Desktop Accessibility': f"{int(results_data['Desktop Metrics'].get('Accessibility', 0) * 100)}%",
                    'Desktop Best Practices': f"{int(results_data['Desktop Metrics'].get('Best Practices', 0) * 100)}%",
                    'Desktop SEO': f"{int(results_data['Desktop Metrics'].get('SEO', 0) * 100)}%"
                }
                
                # Create DataFrame
                results_df = pd.DataFrame([flattened_data])
                
                # Add AI report if available
                if ai_report:
                    results_df['AI Analysis'] = ai_report
                
                # Add comparison results if available
                if comparison_result:
                    results_df['Competitor Analysis'] = comparison_result
                
                # Download button for results
                st.download_button(
                    label="📥 Download Report",
                    data=results_df.to_csv(index=False).encode('utf-8'),
                    file_name='seo_analysis_report.csv',
                    mime='text/csv'
                )
                
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")
    else:
        st.warning("Please enter both article URL and keyword.")

# Footer
st.markdown("---")
st.markdown("### 📌 How to Use?")
st.markdown("""
1. Enter the article URL you want to analyze
2. Enter your target keyword
3. Click 'Start Analysis' button
4. Review the results and download the report
""") 