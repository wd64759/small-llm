import asyncio
from langchain_core.tools import Tool
from typing import List
from openai import OpenAI
import os
import json

from dotenv import load_dotenv
from pydantic import BaseModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
load_dotenv()

class MCPTool(BaseModel):
    name: str
    description: str
    parameters: dict

class Chatbot:
    def __init__(self, model: str, system_prompt: str, tools: List[MCPTool] = [], context: str = ""):
        self.model = model
        self.messages = [
            {"role": "system", "content": system_prompt},
        ]
        if context and len(context) > 0:
            self.messages.append({"role": "user", "content": context})
        self.tools = tools
        self.temperature = 0
        self.max_iterations = 5  # 防止无限循环

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
        
        for chunk in stream_response:
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
        
        return tool_calls, full_response

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
            print(f"Calling tool: {tool_name} with args: {tool_args}")
            
            # Find and execute the tool
            for tool in self.tools:
                if tool.name == tool_name:
                    try:
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
                            
                        tool_results.append({
                            "tool_call_id": tool_call["id"],
                            "role": "tool",
                            "name": tool_name,
                            "content": str(result)
                        })
                        print(f"Tool result: {result}")
                    except Exception as e:
                        print(f"Tool execution error: {e}")
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
            }
        }
        
        if tools:
            kwargs["tools"] = tools
            
        return client.chat.completions.create(**kwargs)

    async def chat(self, prompt: str):
        """Main chat method that supports multiple tool calls"""
        # Add the user's prompt to messages
        self.messages.append({"role": "user", "content": prompt})
        
        # Convert tools to OpenAI format
        openai_tools = self._convert_tools_to_openai_format()
        print(f"Available tools: {[tool.name for tool in self.tools]}")
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            
            # Make API call
            stream_response = self._make_llm_call(self.messages, openai_tools)
            
            # Process streaming response
            tool_calls, full_response = self._assemble_tool_calls_from_stream(stream_response)
            
            # If no tool calls, we're done
            if not tool_calls:
                if full_response:
                    self.messages.append({"role": "assistant", "content": full_response})
                print("\n--- Conversation complete ---")
                break
            
            # Execute tool calls
            tool_results = await self._execute_tool_calls(tool_calls)
            
            # If no tool results, we're done
            if not tool_results:
                print("\n--- No tool results, conversation complete ---")
                break
        
        if iteration >= self.max_iterations:
            print("\n--- Maximum iterations reached ---")
        
        print("\ndone")

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
    chatbot = Chatbot(model="qwen-max", system_prompt="", tools=tools, context="")
    asyncio.run(chatbot.chat("你好，帮我查一下今天的天气怎么样"))
    print(chatbot.messages)