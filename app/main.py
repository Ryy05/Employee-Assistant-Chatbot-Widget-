# In app/main.py

import os
import shutil
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from .core import ChatbotCore
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Policy AI Agent")

# --- Create an 'uploads' directory if it doesn't exist ---
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)
# --------------------------------------------------------

origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
chatbot = ChatbotCore()

@app.post("/chat")
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

# --- NEW: Endpoint for handling file uploads ---
@app.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Return the path so the bot knows where the file is
        return JSONResponse(content={"file_path": file_path}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": f"Could not save file: {e}"}, status_code=500)
# --------------------------------------------

@app.post("/reset")
async def reset_chat():
    """Clears both the LangChain memory and the task-specific conversation state."""
    chatbot.get_memory().clear()
    chatbot.reset_conversation_state()
    return JSONResponse(content={"status": "Conversation memory and state cleared."})