import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRoute


router = APIRouter(prefix="/llm", tags=["llm"])

@router.post("/sse_request")
async def sse_request(request: Request):
    """
    LLM Request with SSE
    """
    async def sse_generator():
        yield "data: Hello, World!\n\n"
        await asyncio.sleep(1)
        yield "data: Hello, World!\n\n"
    return StreamingResponse(sse_generator(), media_type="text/event-stream", 
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "Content-Type": "text/event-stream"})