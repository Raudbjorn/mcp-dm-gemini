from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

app = FastAPI()

app.mount("/static", StaticFiles(directory="web_ui/static"), name="static")

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
