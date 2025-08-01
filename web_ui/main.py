from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import httpx
import os

app = FastAPI(title="TTRPG Assistant Web UI")

app.mount("/static", StaticFiles(directory="web_ui/static"), name="static")

# Configuration for the backend MCP server
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")

class SearchRequest(BaseModel):
    query: str
    rulebook: Optional[str] = None
    content_type: Optional[str] = None
    max_results: int = 5
    use_hybrid: bool = True

class AddRulebookRequest(BaseModel):
    pdf_path: str
    rulebook_name: str
    system: str

class PersonalityRequest(BaseModel):
    action: str
    system_name: Optional[str] = None
    systems: Optional[List[str]] = None

# HTML Routes
@app.get("/")
async def read_index():
    return FileResponse('web_ui/index.html')

@app.get("/search")
async def read_search():
    return FileResponse('web_ui/search.html')

@app.get("/campaign")
async def read_campaign():
    return FileResponse('web_ui/campaign.html')

@app.get("/add-rulebook")
async def read_add_rulebook():
    return FileResponse('web_ui/add-rulebook.html')

@app.get("/session")
async def read_session():
    return FileResponse('web_ui/session.html')

@app.get("/personality")
async def read_personality():
    return FileResponse('web_ui/personality.html')

# API Routes that proxy to the MCP server
@app.post("/api/search")
async def api_search(request: SearchRequest):
    """Proxy search requests to the MCP server"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{MCP_SERVER_URL}/tools/search",
                json=request.dict(),
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Unable to connect to MCP server: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

@app.post("/api/add-rulebook")
async def api_add_rulebook(request: AddRulebookRequest):
    """Proxy add rulebook requests to the MCP server"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{MCP_SERVER_URL}/tools/add_source",
                json={
                    "pdf_path": request.pdf_path,
                    "rulebook_name": request.rulebook_name,
                    "system": request.system,
                    "source_type": "RULEBOOK"
                },
                timeout=300.0  # Longer timeout for PDF processing
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Unable to connect to MCP server: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

@app.post("/api/personality")
async def api_personality(request: PersonalityRequest):
    """Proxy personality management requests to the MCP server"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{MCP_SERVER_URL}/tools/manage_personality",
                json=request.dict(),
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Unable to connect to MCP server: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

@app.get("/api/health")
async def api_health():
    """Check if the MCP server is accessible"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{MCP_SERVER_URL}/tools/get_search_stats", timeout=5.0)
            response.raise_for_status()
            return {
                "status": "healthy",
                "mcp_server": "connected",
                "mcp_url": MCP_SERVER_URL
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "mcp_server": "disconnected",
                "mcp_url": MCP_SERVER_URL,
                "error": str(e)
            }
