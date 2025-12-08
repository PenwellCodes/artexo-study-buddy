#!/usr/bin/env python3
"""
Run script for the Study Buddy Chat API server.

Usage:
    python run_server.py

Or with uvicorn directly from the app directory:
    cd app && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

import sys
import os

# Change to app directory for proper imports
app_dir = os.path.join(os.path.dirname(__file__), "app")
os.chdir(app_dir)
sys.path.insert(0, app_dir)

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable (Render sets PORT, default to 8001 for local dev)
    port = int(os.getenv("PORT", 8001))
    # Only enable reload in development (when PORT is not set by Render)
    reload = os.getenv("PORT") is None
    
    # Run the FastAPI app
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,  # Enable auto-reload during development only
    )

