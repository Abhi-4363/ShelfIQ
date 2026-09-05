"""
ShelfIQ - Retail Sales & Inventory Copilot
Main Application Entry Point (FastAPI backend + static web server)
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(
    title="ShelfIQ",
    description="Smarter shelves. Better decisions. - Retail Sales & Inventory Copilot",
    version="1.0.0"
)

# Serve static files for frontend UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    """Serve the primary single-page application."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "ShelfIQ API is running. Static files not found."}

@app.get("/api/health")
async def health_check():
    """System health check endpoint."""
    return {"status": "ok", "app": "ShelfIQ", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
