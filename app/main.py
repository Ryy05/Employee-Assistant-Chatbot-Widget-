# In app/main.py

from fastapi import FastAPI, Request
import os # You might not need this if you're only getting from .env
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv # Add this line
from .core import ChatbotCore
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Policy AI Agent")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Create a single, reusable instance of the chatbot core logic
# This loads the models only once when the app starts
chatbot = ChatbotCore()

@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    """Serve the main chat interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def handle_chat(request: Request):
    """Handle incoming chat messages."""
    data = await request.json()
    user_message = data.get("message")

    if not user_message:
        return JSONResponse(content={"error": "No message provided"}, status_code=400)

    try:
        bot_response = chatbot.get_answer(user_message)
        return JSONResponse(content={"response": bot_response})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/reset")
async def reset_chat():
    """Clear the conversation memory."""
    chatbot.get_memory().clear()
    return JSONResponse(content={"status": "Conversation memory has been cleared."})