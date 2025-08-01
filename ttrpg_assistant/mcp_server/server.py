from fastapi import FastAPI, Depends
from .tools import router as tools_router
from .dependencies import get_chroma_manager, get_embedding_service
from ..config_utils import load_config_safe

# Load configuration
config = load_config_safe("config.yaml", {
    'mcp': {
        'server_name': 'TTRPG Assistant MCP Server',
        'version': '1.0.0'
    }
})

# Create FastAPI app
app = FastAPI(
    title=config['mcp']['server_name'],
    version=config['mcp']['version']
)

app.include_router(
    tools_router,
    prefix="/tools"
)

@app.get("/")
async def root():
    return {"message": "TTRPG Assistant MCP Server is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
