import re
from serpapi import GoogleSearch
import os
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import List, Dict, Any
from langchain_core.tools import tool
from dotenv import load_dotenv

try:
    from .web_search_utils import load_webpage
except ImportError:
    from web_search_utils import load_webpage

load_dotenv()

@tool
def search(query: str, top_p: int = 5):
    """
    Search the web using Google Search API
    """
    search = GoogleSearch({
        "engine": "google",
        "q": query,
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "location": "China",
        "hl": "zh-CN",
        "gl": "cn",
        "safe": "active",
        "start": 0,
        "num": top_p,
        "tbm": "nws",
    })
    result = search.get_dict()
    result = result["news_results"]
    rs = []
    for idx, news_item in enumerate(result):
        if "link" not in news_item:
            continue
        item = {
            "source": "google",
            "id": idx,
            "title": news_item["title"],
            "link": news_item["link"],
            "snippet": news_item["snippet"],
            "date": news_item["date"],
        }
        item['content'] = load_webpage(item["link"])
        rs.append(item)
    return rs

if __name__ == "__main__":
    print(search("国内影院票房近期排名？"))