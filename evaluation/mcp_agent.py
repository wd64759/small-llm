import asyncio
import os

from dotenv import load_dotenv
from fastmcp import Client

load_dotenv()

BAIDU_API_KEY = os.getenv("BAIDU_API_KEY")
print(BAIDU_API_KEY)
BAIDU_SEARCH = f"http://appbuilder.baidu.com/v2/ai_search/mcp/sse?api_key={BAIDU_API_KEY}"

site_list = ["eastmoney.com","finance.sina.com.cn"]
# "fund.10jqka.com.cn","sse.com.cn","sina.com.cn"

async def main():
    async with Client(BAIDU_SEARCH) as client:
        tools = await client.list_tools()
        # print("Tools", tools)

        result = await client.call_tool("AIsearch", 
            {
                "query": "今日是2025年8月12日，国内影院票房排名？", 
                "search_domain_filter": site_list,
                "instruction":"返回结果以json格式，包含标题、网站、链接、摘要、时间，并按照时间顺序倒排。不要返回不在给定网站列表中的结果。",
                "resource_type_filter":[{"type":"web", "top_k":5}],
                # "top_p":0.1,
                # "temperature":0.1,
                # "model":"deepseek-r1"
            })
        print("Tool", result)

if __name__ == "__main__":
    asyncio.run(main())
