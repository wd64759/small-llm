import asyncio
from datetime import date, datetime
import re
from typing import List
from langchain_core.tools import Tool, tool
import os

from dotenv import load_dotenv
from fastmcp import Client

try:
    from retriever.web_search_utils import load_webpage
    from retriever.search_tools import SearchInput, SearchOutput
except ImportError:
    from web_search_utils import load_webpage
    from search_tools import SearchInput, SearchOutput

load_dotenv()

BAIDU_API_KEY = os.getenv("BAIDU_API_KEY")
print(BAIDU_API_KEY)
BAIDU_SEARCH = f"http://appbuilder.baidu.com/v2/ai_search/mcp/sse?api_key={BAIDU_API_KEY}"

site_list = ["eastmoney.com","finance.sina.com.cn","fund.10jqka.com.cn","sse.com.cn","sina.com.cn"]

async def _search(query: str, top: int = 5):
    async with Client(BAIDU_SEARCH) as client:
        tools = await client.list_tools()
        # print("Tools", tools)

        result = await client.call_tool("AIsearch", 
            {
                "query": query, 
                "search_filter": {
                    "match": {
                        "site": site_list
                    }
                },
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

class BaiduSearchTool(Tool):
    name: str = "baidu_search"
    description: str = "Search the web using Baidu Search API"
    input: SearchInput
    output: List[SearchOutput]

def search(query: str, top: int = 5):
    """
    Search the web using Baidu Search API (synchronous version)
    """
    import nest_asyncio
    nest_asyncio.apply()
    
    try:
        result = asyncio.run(_search(query, top))
    except Exception as e:
        print(f"Search error: {e}")
        return []

    if result.is_error:
        return result.error_message
    
    rs = []
    for content in result.content:
        if content.type == "text":
            # content_text = content.text.encode("utf-8").decode("unicode_escape")  
            pattern = r'Title:\s*(.+?)\nContent:\s*(.+?)\nURL:\s*(.+?)(?=\n\n|$)'
            matches = re.findall(pattern, content.text)
            for idx, (title, snippet, url) in enumerate(matches):
                try:
                    page_content = load_webpage(url)
                    # 如果内容获取失败，使用 snippet 作为备选
                    if not page_content or "页面加载失败" in page_content or "安全验证" in page_content:
                        page_content = snippet
                        print(f"Using snippet as fallback for {url}")
                except Exception as e:
                    print(f"Error loading content for {url}: {e}")
                    page_content = snippet
                
                rs.append({
                    "source": "baidu",
                    "id": f"{idx}-{title}",
                    "title": title,
                    "link": url,
                    "content": page_content,
                    "snippet": snippet,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
    return rs

if __name__ == "__main__":
    # rs = asyncio.run(search_async("国内影院票房近期排名？"))
    rs = search("A股市场流动性特征与投资策略分析？")
    print(rs)
