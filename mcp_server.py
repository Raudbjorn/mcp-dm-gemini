import uvicorn
from ttrpg_assistant.mcp_server.server import app as mcp_app
from web_ui.main import app as web_ui_app

mcp_app.mount("/ui", web_ui_app)

if __name__ == "__main__":
    uvicorn.run(mcp_app, host="0.0.0.0", port=8000)