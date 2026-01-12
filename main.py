import os
import sys
import logging
import httpx
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger
from knowledge_base import KnowledgeBase

load_dotenv()

# --- Logging Configuration ---
class InterceptHandler(logging.Handler):
    """Redirects standard logging to Loguru."""
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(os.path.join(LOG_DIR, "voice_agent_{time}.log"), rotation="100 MB", level="DEBUG")
logging.basicConfig(handlers=[InterceptHandler()], level=0)
logging.getLogger("uvicorn").handlers = [InterceptHandler()]
logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]

# --- FastAPI App ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Azure Configuration ---
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, DEPLOYMENT_NAME]):
    logger.error("Missing required environment variables. Please check .env file.")
    raise ValueError("Missing required environment variables. Please check .env file.")

# Parse hostname for API calls
hostname = AZURE_OPENAI_ENDPOINT.replace("https://", "").replace("http://", "").rstrip("/")
if "/" in hostname:
    hostname = hostname.split("/")[0]

# --- Knowledge Base ---
# Automatically loads all .txt and .md files from 'knowledge/' folder
kb = KnowledgeBase()  # Uses default 'knowledge/' folder

# --- Models ---
class SearchQuery(BaseModel):
    query: str

class TranscriptLog(BaseModel):
    role: str
    text: str

# --- Endpoints ---
@app.post("/log_transcript")
async def log_transcript(log: TranscriptLog):
    """Log user/agent speech from the client."""
    logger.info(f"[TRANSCRIPT] {log.role.upper()}: {log.text}")
    return JSONResponse({"status": "logged"})
@app.get("/")
async def get():
    with open("index.html", "r") as f:
        return HTMLResponse(f.read())

@app.get("/config")
async def get_config():
    """Returns Azure configuration for the frontend (including API key for direct WebRTC)."""
    return JSONResponse(content={
        "hostname": hostname,
        "deployment": DEPLOYMENT_NAME,
        "apiKey": AZURE_OPENAI_API_KEY  # For direct WebRTC auth
    })

@app.get("/session")
async def get_session_token():
    """
    Fetches an ephemeral token from Azure OpenAI for the WebRTC client.
    The browser will use this token to connect directly to Azure.
    """
    logger.info("Fetching ephemeral session token from Azure...")
    
    token_url = f"https://{hostname}/openai/v1/realtime/client_secrets"
    headers = {
        "api-key": AZURE_OPENAI_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Session config
    session_config = {
        "session": {
            "type": "realtime",
            "model": DEPLOYMENT_NAME,
            "input_audio_transcription": {
                "model": "whisper-1"
            },
            "instructions": (
                "You are a senior concierge voice agent for Aeroméxico airlines, providing expert customer service. "
                "1. LANGUAGE: Detect the user's language and respond in the same language. "
                "2. STYLE: Be professional, empathetic, concise (1-2 sentences per response), and use natural contractions (e.g., can't, don't). "
                "3. KNOWLEDGE: For any questions about Aeroméxico flights, bookings, baggage policies, fare families, loyalty programs (Aeroméxico Rewards), "
                "special services (e.g., pets, unaccompanied minors), documentation, onboard amenities, or operational details (e.g., Delta JV status, MEX lounges), "
                "use the search_knowledge_base tool with a precise query to retrieve accurate info from the knowledge base. Do not speculate; base answers on KB results. "
                "If info is unclear or unavailable, politely suggest contacting human support via phone or WhatsApp. "
                "4. GENERAL: Greet users warmly, confirm understanding, and offer proactive help (e.g., 'Would you like to check baggage fees for your route?')."
            ),
            "audio": {
                "output": {
                    "voice": "shimmer"  # Professional, bright voice suitable for customer service
                }
            },
            "tools": [
                {
                    "type": "function",
                    "name": "search_knowledge_base",
                    "description": "Searches the Aeroméxico knowledge base for information on flights, baggage, policies, loyalty, and services.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find relevant information in the knowledge base."
                            }
                        },
                        "required": ["query"]
                    }
                }
            ],
            "tool_choice": "auto"
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, headers=headers, json=session_config, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            logger.info("Successfully obtained ephemeral token.")
            # Token is in data.value per Microsoft docs
            return JSONResponse(content={
                "token": data.get("value"),
                "expires_at": data.get("expires_at"),
                "session_id": data.get("id")
            })
    except httpx.HTTPStatusError as e:
        logger.error(f"Azure token request failed: {e.response.status_code} - {e.response.text}")
        return JSONResponse(content={"error": str(e)}, status_code=e.response.status_code)
    except Exception as e:
        logger.error(f"Token fetch error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/search_kb")
async def search_knowledge_base(query: SearchQuery):
    """
    Searches the local knowledge base and returns results.
    Called by the frontend when the AI triggers the tool.
    """
    logger.info(f"Aeroméxico KB Search Request: '{query.query}'")
    result = kb.search(query.query)
    logger.debug(f"KB Result: {result[:200]}...")
    return JSONResponse(content={"result": result})

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server (WebRTC Mode)...")
    uvicorn.run(app, host="0.0.0.0", port=8000)