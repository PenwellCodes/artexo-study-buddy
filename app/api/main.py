from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os

from services.chat_service import ChatService

# Initialize FastAPI app
app = FastAPI(title="Study Buddy Chat API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chat service
chat_service = ChatService()


# Request/Response models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


class SessionResponse(BaseModel):
    session_id: str


class MessageHistory(BaseModel):
    messages: list


class SessionSummary(BaseModel):
    session_id: str
    last_message_time: Optional[str] = None
    message_count: int
    preview: str
    first_message: Optional[str] = None


class SessionsList(BaseModel):
    sessions: List[SessionSummary]


# API Endpoints
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """
    Send a message and receive a response.
    Creates a new session if session_id is not provided.
    """
    import logging

    try:
        # Create new session if needed or if provided session doesn't exist
        if not request.session_id:
            session_id = chat_service.create_session()
        else:
            session_id = request.session_id
            # If session doesn't exist (e.g., server restarted), create a new one
            if session_id not in chat_service.sessions:
                logging.warning(f"Session {session_id} not found, creating new session")
                session_id = chat_service.create_session()

        # Generate response
        response_text = chat_service.generate_response(session_id, request.message)

        return ChatResponse(response=response_text, session_id=session_id)
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        logging.error(f"ValueError in chat endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/chat/new", response_model=SessionResponse)
async def new_chat():
    """Start a new conversation session."""
    try:
        session_id = chat_service.create_session()
        return SessionResponse(session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/sessions", response_model=SessionsList)
async def list_sessions(limit: Optional[int] = 50):
    """List all chat sessions with summary information."""
    import logging

    try:
        sessions = chat_service.list_sessions(limit=limit)
        # Convert to SessionSummary objects with error handling
        session_summaries = []
        for session in sessions:
            try:
                # Ensure all required fields are present with defaults
                summary = SessionSummary(
                    session_id=session.get("session_id", ""),
                    last_message_time=session.get("last_message_time"),
                    message_count=session.get("message_count", 0),
                    preview=session.get("preview", "New conversation"),
                    first_message=session.get("first_message"),
                )
                session_summaries.append(summary)
            except Exception as e:
                logging.warning(
                    f"Error creating session summary: {str(e)}, session data: {session}"
                )
                continue

        return SessionsList(sessions=session_summaries)
    except Exception as e:
        logging.error(f"Error listing sessions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/{session_id}", response_model=MessageHistory)
async def get_chat_history(session_id: str):
    """Get conversation history for a session."""
    try:
        history = chat_service.get_history(session_id)
        # Format messages for response (remove timestamp for cleaner response)
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
        return MessageHistory(messages=messages)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/{session_id}")
async def delete_chat(session_id: str):
    """Delete a conversation session."""
    try:
        chat_service.delete_session(session_id)
        return {"message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve static files
# Get the project root directory (two levels up from app/api/main.py)
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(app_dir)
static_dir = os.path.join(project_root, "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def read_root():
        """Serve the main HTML file."""
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Static files not found"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
