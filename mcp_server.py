import uvicorn
from ttrpg_assistant.mcp_server.server import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
