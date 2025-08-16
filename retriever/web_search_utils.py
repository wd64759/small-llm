import re
from bs4 import BeautifulSoup
import requests


UNWANTED_TAGS = [
    "script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript", "a", "button",
    "input", "img", "meta", "link", "svg", "figure", "figcaption", "video", "audio", "canvas", "path"
]

UNWANTED_CLASSNAMES = ["post_top", "tie-areas", "post_comment", "post_recommends", "post_side", "N-nav-bottom",
                        "pinglunbox"
]

def load_webpage(url: str):
    """
    Load the webpage from the url using requests + BeautifulSoup
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted tags
        for tag in UNWANTED_TAGS:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Remove unwanted class names
        for classname in UNWANTED_CLASSNAMES:
            for element in soup.find_all(class_=classname):
                element.decompose()
        
        # Get clean text content
        text = soup.get_text(separator=' ', strip=True)
        # Clean up extra whitespace
        text = ' '.join(text.split())
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', '', text)
        return text
    except Exception as e:
        print(f"Error loading webpage: {e}")
        return ""