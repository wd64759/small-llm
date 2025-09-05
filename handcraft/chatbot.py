import asyncio
import logging
import threading
import time
from typing import List
from openai import OpenAI
import os
import json

from dotenv import load_dotenv
from pydantic import BaseModel
from mcp import ClientSession, StdioServerParameters, stdio_client

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handcraft.chat_report import ChatReport, ToolCall
from utils.helper import get_uuid
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 输出到控制台
    ]
)

logger = logging.getLogger(__name__)

thread_local = threading.local()
thread_local.tool_call_index = 1

class MCPTool(BaseModel):
    name: str
    description: str
    parameters: dict

class Chatbot:
    def __init__(self, model: str, system_prompt: str, tools: List[MCPTool] = [], context: str = "", depth_thinking: bool = False, debug: bool = False):
        self.model = model
        self.messages = [
            {"role": "system", "content": system_prompt},
        ]
        if context and len(context) > 0:
            self.messages.append({"role": "user", "content": context})
        self.tools = tools
        self.temperature = 0.2
        self.max_iterations = 5  # 防止无限循环
        self.depth_thinking = depth_thinking
        self.debug = debug
        
    def _convert_tools_to_openai_format(self):
        """Convert tools to OpenAI format"""
        openai_tools = []
        for tool in self.tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return openai_tools

    def _assemble_tool_calls_from_stream(self, stream_response):
        """Assemble complete tool calls from streaming response"""
        current_tool_calls = {}
        full_response = ""
        total_tokens = 0
        
        for chunk in stream_response:
            # DashScope API 的 usage 信息可能在不同位置
            if hasattr(chunk, 'usage') and chunk.usage is not None:
                if hasattr(chunk.usage, 'total_tokens'):
                    total_tokens = chunk.usage.total_tokens
                else:
                    print(f"Usage object exists but no total_tokens attribute")
            
            # 检查 choices 是否为空
            if not chunk.choices or len(chunk.choices) == 0:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                print(delta.content, end="", flush=True)
                full_response += delta.content
            elif delta and delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    # Initialize tool call if not exists
                    if tool_call_delta.index not in current_tool_calls:
                        current_tool_calls[tool_call_delta.index] = {
                            "id": "",
                            "type": "function",
                            "function": {
                                "name": "",
                                "arguments": ""
                            }
                        }
                    
                    # Update tool call with delta information
                    if tool_call_delta.id:
                        current_tool_calls[tool_call_delta.index]["id"] = tool_call_delta.id
                    if tool_call_delta.function:
                        if tool_call_delta.function.name:
                            current_tool_calls[tool_call_delta.index]["function"]["name"] = tool_call_delta.function.name
                        # 在流式输出中有可能存在参数被截断的问题，所以需要累加
                        if tool_call_delta.function.arguments:
                            current_tool_calls[tool_call_delta.index]["function"]["arguments"] += tool_call_delta.function.arguments
        
        # Convert completed tool calls to proper format
        tool_calls = []
        for index, tool_call_data in current_tool_calls.items():
            if tool_call_data["function"]["name"]:  # Only add if name is not empty
                tool_calls.append(tool_call_data)
        
        return tool_calls, full_response, total_tokens

    async def _execute_tool_calls(self, tool_calls):
        """Execute tool calls and return results"""
        if not tool_calls:
            return []
            
        print("\nExecuting tool calls...")
        tool_results = []
        
        # Add the assistant's tool call message to the conversation
        tool_call_message = {
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls
        }
        self.messages.append(tool_call_message)
        
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = tool_call["function"]["arguments"]
            logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
            
            # Find and execute the tool
            for tool in self.tools:
                if tool.name == tool_name:
                    try:
                        start_time = time.time()
                        # Parse arguments if provided
                        args = {}
                        if tool_args:
                            args = json.loads(tool_args)
                        
                        # Call the tool function with arguments
                        if hasattr(tool, "func"):
                            if args:
                                result = tool.func(**args)
                            else:
                                result = tool.func()
                        else:
                            result = await mcp_tool_call(tool_name, args)
                        

                        tool_call_record = ToolCall(tool_name, thread_local.tool_call_index, args, str(result), time.time() - start_time)
                        thread_local.tool_call_index += 1
                        thread_local.llm_call.add_tool_call(tool_call_record)

                        tool_results.append({
                            "tool_call_id": tool_call["id"],
                            "role": "tool",
                            "name": tool_name,
                            "content": str(result)
                        })
                    except Exception as e:
                        logger.error(f"Tool {tool_name} execution error: {e}")
                    break
        
        # Add tool results to messages
        for result in tool_results:
            self.messages.append(result)
            
        return tool_results

    def _make_llm_call(self, messages, tools=None):
        """Make API call and return response"""
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url=os.getenv("DASHSCOPE_API_URL")
        )
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": self.temperature,
            "stream_options": {
                "include_usage": True
            },
            # "has_thoughts": self.depth_thinking and self.debug
        }
        kwargs["extra_body"] = {"enable_thinking": self.depth_thinking}
        
        if tools:
            kwargs["tools"] = tools
        return client.chat.completions.create(**kwargs)

    async def chat(self, prompt: str) -> ChatReport:
        """Main chat method that supports multiple tool calls"""
        # Add the user's prompt to messages
        self.messages.append({"role": "user", "content": prompt})
        total_tokens = 0
        chat_report = ChatReport()
        # Convert tools to OpenAI format
        openai_tools = self._convert_tools_to_openai_format()
        start_time = time.time()
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            llm_call = chat_report.start_llm_call(get_uuid())
            thread_local.llm_call = llm_call
            
            # Make API call
            stream_response = self._make_llm_call(self.messages, openai_tools)
            end_time = time.time()
            
            # Process streaming response
            tool_calls, full_response, total_tokens_from_stream = self._assemble_tool_calls_from_stream(stream_response)
            llm_call.complete(prompt, full_response, end_time - start_time, total_tokens_from_stream)
            total_tokens += total_tokens_from_stream
            # If no tool calls, we're done
            if not tool_calls:
                if full_response:
                    self.messages.append({"role": "assistant", "content": full_response})
                break
            
            # Execute tool calls
            tool_results = await self._execute_tool_calls(tool_calls)
            # If no tool results, we're done
            if not tool_results:
                logger.info("\n--- No tool results, conversation complete ---")
                break
        
        if iteration >= self.max_iterations:
            logger.info("\n--- Maximum iterations reached ---")
        
        logger.info(f"Total tokens: {total_tokens}")
        thread_local.llm_call = None
        thread_local.tool_call_index = 1
        return chat_report

async def mcp_tool_call(tool_name: str, args: dict):
    params = StdioServerParameters(
        command="/Users/dongwei/Library/Caches/pypoetry/virtualenvs/langchain-project-y8rcUVU--py3.12/bin/python",
        args=["handcraft/mcp_tools.py"]
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = await session.call_tool(tool_name, args)
            return response

if __name__ == "__main__":

    
    async def main():
        params = StdioServerParameters(
            command="/Users/dongwei/Library/Caches/pypoetry/virtualenvs/langchain-project-y8rcUVU--py3.12/bin/python",
            args=["handcraft/mcp_tools.py"]
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                print("Tools", tools)
                response = await session.call_tool("get_weather", {"location": "北京"})
                print("Response", response)
                return tools
    
    list_tools = asyncio.run(main())
    tools = [MCPTool(name=tool.name, description=tool.description, parameters=tool.inputSchema) for tool in list_tools.tools]
    chatbot = Chatbot(model="qwen-max", system_prompt="", tools=tools, context="", depth_thinking=True, debug=True)
    chat_report = asyncio.run(chatbot.chat("你好，帮我查一下今天的天气怎么样"))
    logger.info(json.dumps(chat_report.to_dict(), ensure_ascii=False, indent=4))