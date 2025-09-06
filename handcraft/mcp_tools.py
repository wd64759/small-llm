import os
from mcp.server.fastmcp import FastMCP

from dotenv import load_dotenv

load_dotenv()

app = FastMCP()

@app.tool()
def get_location():
    """
    Get user's location
    """
    return "北京"

@app.tool()
def get_weather(location: str = "北京"):
    """
    Get the weather for a specific location
    Args:
        location: The location to get the weather for
    Returns:
        The weather for the specific location
    """
    return f"{location}的天气是：多云，34度，湿度80%，下午有短时阵雨。"

@app.tool()
def get_news(location: str):
    """
    Get the latest news for a specific location
    Args:
        location: The location to get news for
    Returns:
        The latest news for the specific location
    """
    return f"{location}新闻，今天沪深股市大涨200点。"

if __name__ == "__main__":
    app.run()
