from datetime import datetime
import os
import sys
import asyncio
from mcp.server.fastmcp import FastMCP

from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入百度搜索工具
from retriever.baidu_search import search

load_dotenv()

app = FastMCP()

@app.tool()
def get_current_time():
    """
    Get the current time
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@app.tool()
def get_location():
    """
    Get user's location
    """
    return "北京"

@app.tool()
def get_weather(location: str):
    """
    Get the weather for a specific location
    Args:
        location: The location to get the weather for
    Returns:
        The weather for the specific location
    """
    return f"{location}的天气是：多云，34度，湿度80%，下午有短时阵雨。"

@app.tool()
def baidu_search(query: str, top: int = 5):
    """
    Search the web using Baidu Search API for financial and news information
    Args:
        query: The search query
        top: Number of results to return (default: 5)
    Returns:
        List of search results with title, link, content, snippet and date
    """
    try:
        results = search(query, top)
        if not results:
            return "未找到相关搜索结果"
        
        # 格式化结果
        formatted_results = []
        for result in results:
            formatted_results.append({
                "title": result.get("title", ""),
                "link": result.get("link", ""),
                "snippet": result.get("snippet", ""),
                "content": result.get("content", "")[:500] + "..." if len(result.get("content", "")) > 500 else result.get("content", ""),
                "date": result.get("date", ""),
                "source": result.get("source", "baidu")
            })
        
        return formatted_results
    except Exception as e:
        return f"搜索出错: {str(e)}"

@app.tool()
def get_news(location: str, query: str, top: int = 5):
    """
    Get the latest news for a specific location using Baidu search
    Args:
        location: The location to get news for
    Returns:
        The latest news for the specific location
    """
    try:
        # 使用百度搜索获取新闻
        search_query = f"{location} {query}"
        results = search(search_query, top=top)
        
        if not results:
            return f"{query} 未找到相关搜索结果"
        
        # 格式化新闻结果
        news_summary = f"{location} {query}：\n\n"
        for i, result in enumerate(results[:3], 1):
            news_summary += f"{i}. {result.get('title', '')}\n"
            news_summary += f"   {result.get('snippet', '')}\n"
            news_summary += f"   来源: {result.get('link', '')}\n\n"
        return news_summary
    except Exception as e:
        return f"{location} {query} 搜索出错: {str(e)}"


if __name__ == "__main__":
    app.run()
