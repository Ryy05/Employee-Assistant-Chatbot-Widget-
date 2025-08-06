# In app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from .core import ChatbotCore

# --- IMPORT THE CORS MIDDLEWARE ---
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(title="Policy AI Agent")

# --- ADD THE CORS CONFIGURATION ---
# This allows your frontend at localhost:8000 to talk to this backend
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)
# ----------------------------------

# This line is for serving static files like your logo if needed.
# We will run the server from the root, so the path is relative.
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create a single, reusable instance of the chatbot core logic
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