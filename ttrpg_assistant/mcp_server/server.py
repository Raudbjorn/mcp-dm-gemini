from fastapi import FastAPI, Depends
import yaml
from .tools import router as tools_router
from .dependencies import get_redis_manager, get_embedding_service

# Load configuration
with open("config/config.yaml", 'r') as f:
    config = yaml.safe_load(f)

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
