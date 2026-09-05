"""
ShelfIQ - Retail Sales & Inventory Copilot
Main Application Entry Point (FastAPI backend + static web server)
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from src.data_loader import DataLoader
from src.analytics import AnalyticsEngine
from src.rules import AttentionEngine
from src.api import create_api_router

app = FastAPI(
    title="ShelfIQ",
    description="Smarter shelves. Better decisions. - Retail Sales & Inventory Copilot API",
    version="1.0.0"
)

# CORS Configuration for local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Data, Analytics, and Business Attention Engines on startup (cached in memory)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
data_loader = DataLoader(DATA_DIR)
is_valid, validation_result = data_loader.load_all_data()

analytics_engine = AnalyticsEngine(data_loader)
attention_engine = AttentionEngine(analytics_engine)

# Register API routes from src/api.py
api_router = create_api_router(data_loader, analytics_engine, attention_engine)
app.include_router(api_router)

# Serve static files for frontend UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    """Root endpoint returning ShelfIQ application status."""
    index_path = os.path.join(static_dir, "index.html")
    # If browser requests HTML (Accept header contains text/html), serve UI
    # Otherwise return app status JSON
    return {
        "name": "ShelfIQ",
        "status": "running",
        "version": "1.0.0",
        "tagline": "Smarter shelves. Better decisions.",
        "docs_url": "http://localhost:8000/docs"
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting ShelfIQ server on http://localhost:8000 ...")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
