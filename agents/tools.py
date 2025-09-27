from langchain.tools import BaseTool
from langchain_community.chat_models import ChatOpenAI
from typing import Optional, List, Dict, Any
from config.env import Config
import datetime
import logging

logger = logging.getLogger(__name__)

class WebSearchTool(BaseTool):
    """Tool for searching the web"""
    
    name:str = "web_search"
    description:str = "Search the web for current information"
    
    def _run(self, query: str) -> str:
        """Execute the web search"""
        try:
            # This is a placeholder - you would integrate with a real search API
            # like SerpAPI, Google Custom Search, etc.
            return f"Search results for: {query}\n[Placeholder - integrate with real search API]"
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return f"Error searching web: {str(e)}"
    
    def _arun(self, query: str) -> str:
        """Async version of the tool"""
        return self._run(query)

class CalculatorTool(BaseTool):
    """Tool for mathematical calculations"""
    
    name:str = "calculator"
    description:str = "Perform mathematical calculations"
    
    def _run(self, expression: str) -> str:
        """Execute the calculation"""
        try:
            # Basic safety check - only allow basic math operations
            allowed_chars = set('0123456789+-*/(). ')
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression"
            
            result = eval(expression)
            return f"Result: {result}"
        except Exception as e:
            logger.error(f"Error in calculation: {e}")
            return f"Error calculating: {str(e)}"
    
    def _arun(self, expression: str) -> str:
        """Async version of the tool"""
        return self._run(expression)

class DateTimeTool(BaseTool):
    """Tool for getting current date and time"""
    
    name:str = "datetime"
    description:str = "Get current date and time information"
    
    def _run(self, timezone: str = "UTC") -> str:
        """Get current datetime"""
        try:
            now = datetime.datetime.now()
            return f"Current datetime: {now.strftime('%Y-%m-%d %H:%M:%S')} ({timezone})"
        except Exception as e:
            logger.error(f"Error getting datetime: {e}")
            return f"Error getting datetime: {str(e)}"
    
    def _arun(self, timezone: str = "UTC") -> str:
        """Async version of the tool"""
        return self._run(timezone)

class WeatherTool(BaseTool):
    """Tool for getting weather information"""
    
    name:str = "weather"
    description:str = "Get weather information for a location"
    
    def _run(self, location: str) -> str:
        """Get weather for location"""
        try:
            # This is a placeholder - you would integrate with a weather API
            # like OpenWeatherMap, WeatherAPI, etc.
            return f"Weather for {location}:\n[Placeholder - integrate with real weather API]"
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            return f"Error getting weather: {str(e)}"
    
    def _arun(self, location: str) -> str:
        """Async version of the tool"""
        return self._run(location)

class FileReadTool(BaseTool):
    """Tool for reading files"""
    
    name:str = "file_read"
    description:str = "Read contents of a file"
    
    def _run(self, file_path: str) -> str:
        """Read file contents"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"File contents of {file_path}:\n{content}"
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return f"Error reading file: {str(e)}"
    
    def _arun(self, file_path: str) -> str:
        """Async version of the tool"""
        return self._run(file_path)

def get_default_tools() -> List[BaseTool]:
    """Get list of default tools"""
    return [
        CalculatorTool(),
        DateTimeTool(),
        WeatherTool(),
        WebSearchTool(),
        FileReadTool()
    ]

def create_custom_tool(name: str, description: str, func) -> BaseTool:
    """Create a custom tool from a function"""
    
    class CustomTool(BaseTool):
        name: str = name
        description: str = description
        
        def _run(self, *args, **kwargs):
            return func(*args, **kwargs)
        
        def _arun(self, *args, **kwargs):
            return self._run(*args, **kwargs)
    
    return CustomTool() 

def create_llm_model(model_name: str, llm_args: dict):
    # by default, enable_thinking is False
    if "enable_thinking" in llm_args:
        llm_args["extra_body"] = {"enable_thinking": llm_args.pop("enable_thinking")}
    else:
        llm_args["extra_body"] = {"enable_thinking": False}

    """Create a LLM model"""
    return ChatOpenAI(
                model=model_name,
                base_url=Config.OPENAI_BASE_URL,
                api_key=Config.OPENAI_API_KEY,
                temperature=llm_args.pop("temperature", 0.1),
                **{k: v for k, v in llm_args.items() if k != "model"}
            )