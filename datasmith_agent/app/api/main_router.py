from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from ..core.orchestrator import AgentOrchestrator 
from ..core.models import AgentResponse           
from typing import Optional
from pathlib import Path

router = APIRouter()
orchestrator = AgentOrchestrator()

# Define the absolute path to the templates folder
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "templates" / "chat_ui.html"

@router.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serves the simple chat-like UI."""
    try:
        # Use the absolute path defined above
        with open(TEMPLATE_PATH, "r") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(f"<h1>Error: chat_ui.html not found at path: {TEMPLATE_PATH}</h1>")

@router.post("/process", response_model=AgentResponse)
async def process_submission(
    query: str = Form(""),
    file: Optional[UploadFile] = File(None)
):
    """Main endpoint to process user queries and file uploads."""
    if not query.strip() and not file:
        return AgentResponse(
            status="Error",
            extracted_text="",
            result="Please provide text or upload a file.",
            log=["No input provided."]
        )

    response = await orchestrator.run(query, file)
    return response