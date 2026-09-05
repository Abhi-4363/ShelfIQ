"""
ShelfIQ - Retail Sales & Inventory Copilot
Main Application Entry Point (FastAPI backend + static web server)
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.data_loader import DataLoader

app = FastAPI(
    title="ShelfIQ",
    description="Smarter shelves. Better decisions. - Retail Sales & Inventory Copilot",
    version="1.0.0"
)

# Initialize and validate data on startup
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
data_loader = DataLoader(DATA_DIR)
is_valid, validation_result = data_loader.load_all_data()

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
    return {
        "status": "ok",
        "app": "ShelfIQ",
        "version": "1.0.0",
        "data_loaded": data_loader.is_loaded,
        "data_valid": is_valid
    }

@app.get("/api/data/status")
async def data_status():
    """Endpoint returning dataset loading and validation status."""
    if not validation_result:
        return {"loaded": False, "valid": False}
    
    return {
        "loaded": data_loader.is_loaded,
        "is_valid": validation_result.is_valid,
        "summary_stats": validation_result.summary_stats,
        "errors_count": len(validation_result.errors),
        "warnings_count": len(validation_result.warnings),
        "errors": [
            {
                "file_name": e.file_name,
                "row_index": e.row_index,
                "field_name": e.field_name,
                "message": e.message
            }
            for e in validation_result.errors
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
