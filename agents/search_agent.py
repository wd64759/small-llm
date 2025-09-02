from langchain.agents import create_react_agent
from agents.base_agent import BaseAgent
from retriever.baidu_search import BaiduSearchTool
from config.env import Config

class SearchAgent(BaseAgent):
    def __init__(self, name: str = "search_agent", description: str = "A search agent that can search the web for latest information"):
        super().__init__(name, description)
        self.tools = [BaiduSearchTool()]
        self.llm_model = {
            "model": "qwen-3.5-32b",
            "temperature": 0,
            "max_tokens": 1024,
        }


    def run(self, query: str, extra_params: dict = {}):
        agent_executor = create_react_agent(
            model=self.llm_model,
            tools=self.tools,
            prompt=self.prepare_prompt(query, self.get_context(query, extra_params)),  # 🔥 关键修改：直接传入prompt
            checkpointer=MemorySaver(),
            # version="v1",
            debug=Config.IS_DEBUG_MODE
    )
