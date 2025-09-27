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
        reasoning_content = ""
        full_response = ""
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0

        for chunk in stream_response:
            # DashScope API 的 usage 信息可能在不同位置
            if not chunk.choices:
                if hasattr(chunk.usage, 'total_tokens'):
                    total_tokens = chunk.usage.total_tokens
                if hasattr(chunk.usage, 'prompt_tokens'):
                    prompt_tokens = chunk.usage.prompt_tokens
                if hasattr(chunk.usage, 'completion_tokens'):
                    completion_tokens = chunk.usage.completion_tokens
                continue

            # 检查 choices 是否为空
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                reasoning_content += delta.reasoning_content
            
            if hasattr(delta, "content") and delta.content:
                full_response += delta.content
            elif hasattr(delta, "tool_calls") and delta.tool_calls:
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
        
        return tool_calls, full_response, reasoning_content, {"total_tokens": total_tokens, "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}

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
                        
                        reformat_result = {
                            "structured_output": result.structuredContent if hasattr(result, "structuredContent") else None,
                            "text": " ".join(t.text for t in result.content) if hasattr(result, "content") else "",
                            "error": result.isError if hasattr(result, "isError") else False
                        }
                        tool_call_record = ToolCall(tool_name, thread_local.tool_call_index, args, reformat_result, time.time() - start_time)
                        thread_local.tool_call_index += 1
                        thread_local.llm_call.add_tool_call(tool_call_record)

                        # 检查工具调用是否是错误的，如果是错误，则直接返回错误信息
                        content = ""
                        if result.isError:
                            content = result.content[0].text if hasattr(result, "content") and result.content else ""
                        else:
                            content = result.structuredContent if hasattr(result, "structuredContent") and result.structuredContent else " ".join(t.text for t in result.content) if hasattr(result, "content") else ""

                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": tool_name,
                            "content": content
                        })
                    except Exception as e:
                        logger.error(f"Tool {tool_name} execution error: {e}", e)
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
            "extra_body": {
                "enable_thinking": self.depth_thinking,
                "enable_search": False
            }
        }
        
        if tools:
            kwargs["tools"] = tools
        return client.chat.completions.create(**kwargs)

    async def chat(self, prompt: str) -> ChatReport:
        """Main chat method that supports multiple tool calls"""
        # Add the user's prompt to messages
        self.messages.append({"role": "user", "content": prompt})
        total_tokens = 0
        chat_report = ChatReport()
        # 初始化线程本地变量
        thread_local.session_id = get_uuid()
        thread_local.tool_call_index = 1
        # Convert tools to OpenAI format
        openai_tools = self._convert_tools_to_openai_format()
        start_time = time.time()
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            llm_call = chat_report.start_llm_call(thread_local.session_id)
            thread_local.llm_call = llm_call
            
            # Make API call
            stream_response = self._make_llm_call(self.messages, openai_tools)
            end_time = time.time()
            
            # Process streaming response
            tool_calls, full_response, reasoning_content, token_usage = self._assemble_tool_calls_from_stream(stream_response)
            llm_call.complete("".join([message.get("content", "") or "" for message in self.messages]), full_response, reasoning_content, end_time - start_time, token_usage)
            total_tokens += token_usage["total_tokens"]
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
        chat_report.total_tokens = total_tokens
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
    chatbot = Chatbot(model="qwen3-32b", system_prompt="你是一个金融领域专家，请根据用户的问题进行分析，并给出具体的建议。在回答问题时，请给出你的思考过程信息。", tools=tools, context="", depth_thinking=True, debug=True)
    chat_report = asyncio.run(chatbot.chat("本金100万如何进行股票投资，最多承受20%的回撤"))
    logger.info(json.dumps(chat_report.to_dict(), ensure_ascii=False, indent=4))