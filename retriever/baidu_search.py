import asyncio
from datetime import date, datetime
import re
from langchain_core.tools import tool
import os

from dotenv import load_dotenv
from fastmcp import Client

try:
    from .web_search_utils import load_webpage
except ImportError:
    from web_search_utils import load_webpage

load_dotenv()

BAIDU_API_KEY = os.getenv("BAIDU_API_KEY")
print(BAIDU_API_KEY)
BAIDU_SEARCH = f"http://appbuilder.baidu.com/v2/ai_search/mcp/sse?api_key={BAIDU_API_KEY}"

site_list = ["eastmoney.com","finance.sina.com.cn"]
# "fund.10jqka.com.cn","sse.com.cn","sina.com.cn"

async def _search(query: str, top: int = 5):
    async with Client(BAIDU_SEARCH) as client:
        tools = await client.list_tools()
        # print("Tools", tools)

        result = await client.call_tool("AIsearch", 
            {
                "query": query, 
                "search_domain_filter": site_list,
                # useless for now
                "instruction":"""
                    返回结果按照json格式，
                    {
                        "title": "标题",
                        "link": "链接",
                        "snippet": "摘要",
                        "date": "时间"
                    }
                    按照时间顺序倒排。
                """,
                "resource_type_filter":[{"type":"web", "top_k": top}],
                "search_top_k": top
            }
        )
        return result

@tool
def search(query: str, top: int = 5):
    """
    Search the web using Baidu Search API
    """
    result = asyncio.run(_search(query, top))

    if result.is_error:
        return result.error_message
    
    rs = []
    for content in result.content:
        if content.type == "text":
            # content_text = content.text.encode("utf-8").decode("unicode_escape")  
            pattern = r'Title:\s*(.+?)\nContent:\s*(.+?)\nURL:\s*(.+?)(?=\n\n|$)'
            matches = re.findall(pattern, content.text)
            for idx, (title, snippet, url) in enumerate(matches):
                content = load_webpage(url)
                rs.append({
                    "source": "baidu",
                    "id": f"{idx}-{title}",
                    "title": title,
                    "link": url,
                    "content": content,
                    "snippet": snippet,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
    return rs

async def search_async(query: str, top: int = 5):
    """
    Async version of search function for direct execution
    """
    result = await _search(query, top)
    
    if result.is_error:
        return result.error_message
    
    rs = []
    for content in result.content:
        if content.type == "text":
            # content_text = content.text.encode("utf-8").decode("unicode_escape")  
            blocks = re.split(r'\n\s*\n', content.text.strip())
            for idx, block in enumerate(blocks):
                title = re.search(r'Title: (.*)', block).group(1)
                snippet = re.search(r'Content: (.*)', block).group(1)   
                url = re.search(r'URL: (.*)', block).group(1)
                content = load_webpage(url)
                rs.append({
                    "source": "baidu",
                    "id": f"{idx}-{title}",
                    "title": title,
                    "link": url,
                    "content": content,
                    "snippet": snippet,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                print(rs[-1])
    return rs

if __name__ == "__main__":
    rs = asyncio.run(search_async("国内影院票房近期排名？"))
    print(rs)
