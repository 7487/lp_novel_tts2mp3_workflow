"""FastAPI application entry point."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import settings

app = FastAPI(
    title="Audiobook Production Platform",
    description="Backend API for audiobook production workflow",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    settings.ensure_data_dirs()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Include routers (imported after app creation to avoid circular imports)
def register_routers():
    from routers.books import router as books_router
    from routers.chapters import router as chapters_router
    from routers.segments import router as segments_router
    from routers.logs import router as logs_router

    app.include_router(books_router, prefix="/api/v1")
    app.include_router(chapters_router, prefix="/api/v1")
    app.include_router(segments_router, prefix="/api/v1")
    app.include_router(logs_router, prefix="/api/v1")


register_routers()

# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
