from langchain.agents import initialize_agent, AgentType
from langchain_community.llms import OpenAI
from langchain.tools import BaseTool
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ReActAgent:
    """ReAct (Reasoning and Acting) Agent"""
    
    def __init__(self, tools: List[BaseTool], model_name: str = "gpt-3.5-turbo"):
        """
        Initialize ReAct Agent
        
        Args:
            tools: List of tools the agent can use
            model_name: OpenAI model name
        """
        self.tools = tools
        self.llm = OpenAI(model_name=model_name, temperature=0)
        self.agent = None
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the ReAct agent"""
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.REACT_DOCSTORE,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the agent with a query
        
        Args:
            query: User query
            
        Returns:
            Dictionary containing agent response and execution details
        """
        try:
            result = self.agent.run(query)
            return {
                "answer": result,
                "success": True,
                "agent_type": "react"
            }
        except Exception as e:
            logger.error(f"Error in ReAct agent: {e}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "success": False,
                "agent_type": "react"
            }
    
    def add_tool(self, tool: BaseTool):
        """Add a new tool to the agent"""
        self.tools.append(tool)
        self._setup_agent()  # Reinitialize with new tools
    
    def get_tools(self) -> List[BaseTool]:
        """Get list of available tools"""
        return self.tools 