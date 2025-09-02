import asyncio
from langchain_core.tools import Tool
from typing import List
from openai import OpenAI
import os
import json

from dotenv import load_dotenv
load_dotenv()

class Chatbot:
    def __init__(self, model: str, system_prompt: str, tools: List[dict] = [], context: str = ""):
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
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
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
                        if tool_call_delta.function.arguments:
                            current_tool_calls[tool_call_delta.index]["function"]["arguments"] += tool_call_delta.function.arguments
                    
                    print("tool_call>>>>>>>>>>>>>>>>")
                    print(f"Index: {tool_call_delta.index}, Name: {current_tool_calls[tool_call_delta.index]['function']['name']}")
        
        # Convert completed tool calls to proper format
        tool_calls = []
        for index, tool_call_data in current_tool_calls.items():
            if tool_call_data["function"]["name"]:  # Only add if name is not empty
                tool_calls.append(tool_call_data)
        
        return tool_calls, full_response

    def _execute_tool_calls(self, tool_calls):
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
                if tool["name"] == tool_name:
                    try:
                        # Parse arguments if provided
                        args = {}
                        if tool_args:
                            args = json.loads(tool_args)
                        
                        # Call the tool function with arguments
                        if args:
                            result = tool["func"](**args)
                        else:
                            result = tool["func"]()
                            
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

    def _make_api_call(self, messages, tools=None):
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
        print(f"Available tools: {[tool['name'] for tool in self.tools]}")
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            
            # Make API call
            stream_response = self._make_api_call(self.messages, openai_tools)
            
            # Process streaming response
            tool_calls, full_response = self._assemble_tool_calls_from_stream(stream_response)
            
            # If no tool calls, we're done
            if not tool_calls:
                if full_response:
                    self.messages.append({"role": "assistant", "content": full_response})
                print("\n--- Conversation complete ---")
                break
            
            # Execute tool calls
            tool_results = self._execute_tool_calls(tool_calls)
            
            # If no tool results, we're done
            if not tool_results:
                print("\n--- No tool results, conversation complete ---")
                break
        
        if iteration >= self.max_iterations:
            print("\n--- Maximum iterations reached ---")
        
        print("\ndone")

def get_location():
    return "北京"

def get_weather(location: str = "北京"):
    return f"{location}今天天气晴朗"

def get_news(location: str):
    return "今天新闻是，北京天气晴朗"

if __name__ == "__main__":
    tools = [
        {
            "name": "get_location", 
            "func": get_location, 
            "description": "Get user's location", 
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_weather", 
            "func": get_weather, 
            "description": "Get the weather for a specific location", 
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location to get the weather for"
                    }
                },
                "required": ["location"]
            }
        }
    ]
    chatbot = Chatbot(model="qwen-max", system_prompt="You are a helpful assistant. You have access to tools that you can use to help answer questions. When you need information that can be obtained through tools, please use them.", tools=tools, context="")
    asyncio.run(chatbot.chat("你好，帮我查一下今天的天气怎么样"))
    print(chatbot.messages)