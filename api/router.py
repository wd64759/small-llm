from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    question: str
    agent_type: Optional[str] = "rag"  # "rag", "react", "function"
    k: Optional[int] = 4

class QueryResponse(BaseModel):
    answer: str
    success: bool
    source_documents: Optional[List[Dict[str, Any]]] = None
    agent_type: Optional[str] = None
    error: Optional[str] = None

class DocumentUploadRequest(BaseModel):
    file_path: str
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200

class DocumentUploadResponse(BaseModel):
    success: bool
    document_count: int
    message: str

# Create router
router = APIRouter(prefix="/api/v1", tags=["langchain"])

# Global variables for components (would be injected via dependency injection in production)
rag_chain = None
react_agent = None
function_agent = None

@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query the system using different agent types
    """
    try:
        if request.agent_type == "rag":
            if not rag_chain:
                raise HTTPException(status_code=500, detail="RAG chain not initialized")
            
            result = rag_chain.query(request.question)
            return QueryResponse(
                answer=result["answer"],
                success=result["success"],
                source_documents=result.get("source_documents", []),
                agent_type="rag"
            )
            
        elif request.agent_type == "react":
            if not react_agent:
                raise HTTPException(status_code=500, detail="ReAct agent not initialized")
            
            result = react_agent.run(request.question)
            return QueryResponse(
                answer=result["answer"],
                success=result["success"],
                agent_type="react"
            )
            
        elif request.agent_type == "function":
            if not function_agent:
                raise HTTPException(status_code=500, detail="Function agent not initialized")
            
            result = function_agent.run(request.question)
            return QueryResponse(
                answer=result["answer"],
                success=result["success"],
                agent_type="function"
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported agent type: {request.agent_type}")
            
    except Exception as e:
        logger.error(f"Error in query endpoint: {e}")
        return QueryResponse(
            answer="",
            success=False,
            error=str(e),
            agent_type=request.agent_type
        )

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_documents(request: DocumentUploadRequest):
    """
    Upload and process documents for the knowledge base
    """
    try:
        # This would integrate with the document loader and vector store
        # For now, return a placeholder response
        return DocumentUploadResponse(
            success=True,
            document_count=1,
            message=f"Document uploaded successfully: {request.file_path}"
        )
    except Exception as e:
        logger.error(f"Error in upload endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "components": {
            "rag_chain": rag_chain is not None,
            "react_agent": react_agent is not None,
            "function_agent": function_agent is not None
        }
    }

@router.get("/tools")
async def get_available_tools():
    """
    Get list of available tools for agents
    """
    try:
        tools = []
        if react_agent:
            tools.extend([tool.name for tool in react_agent.get_tools()])
        if function_agent:
            tools.extend([tool.name for tool in function_agent.get_tools()])
        
        return {
            "tools": list(set(tools)),  # Remove duplicates
            "total_count": len(set(tools))
        }
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dependency injection functions (for production use)
def get_rag_chain():
    """Dependency to get RAG chain"""
    return rag_chain

def get_react_agent():
    """Dependency to get ReAct agent"""
    return react_agent

def get_function_agent():
    """Dependency to get Function agent"""
    return function_agent

# Initialize components (would be called during app startup)
def initialize_components():
    """Initialize all components"""
    global rag_chain, react_agent, function_agent
    
    try:
        # Initialize components here
        # This would typically be done with proper dependency injection
        logger.info("Components initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing components: {e}")
        raise 