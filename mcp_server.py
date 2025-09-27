import asyncio
from typing import List, Literal, MutableMapping, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field, model_validator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from enum import Enum

import uvicorn
import requests

import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

app = FastAPI()

class ToolService(BaseModel):
    name: str = Field(description="The name of the service")
    description: str = Field(description="The description of the service")
    url: str = Field(description="The URL of the service")
    heartbeat: Optional[str] = Field(description="The heartbeat of the service")
    protocol: Literal['http','https','tcp','udp','grpc'] = Field(description="The protocol of the service", default="http")
    version: Optional[str] = Field(description="The version of the service", default="1.0.0")
    @model_validator(mode="after")
    def validate(cls, values):
        pass

    # get the heartbeat url based on the url
    def get_heartbeat(self):
        if self.heartbeat is None:
            return f"{self.url}/health"
        return self.heartbeat

tools: MutableMapping[str, List[ToolService]] = {}

@app.get("/mcp")
def read_root():
    return {"message": "mcp server is running"}

@app.post("/mcp/tools")
def register(service: ToolService):
    """
    Register a service
    This function is used to register a service.
    It will check if the service is already registered.
    If not, it will add the service to the tools list.
    """
    if not validate_service(service):
        return {"error": "service already registered"}
    
    tools[service.name.upper()].append(service)
    return {"message": f"service {service.name} registered", "service": service.model_dump_json()}

@app.get("/mcp/tools")
def get_tools():
    return {"tools": list(tools.keys())}

@app.get("/mcp/tools/{tool_name}")
def get_tool(tool_name: str):
    if tool_name.upper() not in tools:
        return {"error": "service not found"}
    return {"message": tools[tool_name.upper()].model_dump_json()}

def validate_service(service: ToolService):
    tool_name: str = service.name.upper()
    if tool_name in tools:
        for s in tools[tool_name]:
            if s.url == service.url:
                return False
    return True

async def health_check_job():
    """
    Health check job
    This job is used to check the health of the tools.
    It will check the health of the tools and remove the unhealthy tools.
    """
    logger.info("Tools health check job started")
    import time
    for tool_name, tool_list in tools.items():
        for i in range(len(tool_list) - 1, -1, -1):
            tool = tool_list[i]
            key = f"{tool_name}:{tool.url}"
            success = False
            response = None
            for attempt in range(3):
                try:
                    response = requests.get(tool.get_heartbeat(), timeout=3)
                    if response.status_code == 200:
                        success = True
                        break
                except Exception as e:
                    logger.warning(f"Tool {tool_name} ({tool.url}) attempt {attempt + 1} failed: {e}")
                
                if attempt < 2:
                    time.sleep(1)
            
            if not success:
                logger.error(f"Tool {tool_name} ({tool.url}) is not healthy, response: {response}")
                del tool_list[i]

async def init_tools():
    """
    Init tools
    This function is used to init the tools.
    It will init the tools list.
    """
    default_tools = [
        {
            "name": "google_search",
            "description": "Google search",
            "url": "https://www.google.com",
        }
    ]

async def main():
    """
    Registry server
    This server is used to register and manage the tools.
    It will check the health of the tools and remove the unhealthy tools.
    It will also provide the tools list to the client.
    """
    # 创建主协程
    scheduler = AsyncIOScheduler()
    # 添加定时Health检查任务
    scheduler.add_job(health_check_job, "interval", seconds=10)
    # 启动scheduler
    scheduler.start()
    
    # 启动server
    port = 7600
    logger.info(f"Registry server started at http://0.0.0.0:{port}")
    server_config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(server_config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())