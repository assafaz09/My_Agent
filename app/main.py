from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import importlib
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize services
    print("Starting Personal Knowledge Agent...")
    yield
    # Shutdown: Cleanup
    print("Shutting down Personal Knowledge Agent...")

app = FastAPI(
    title="Personal Knowledge Agent",
    description="An AI agent that deeply knows you through uploaded files",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # We don't need credentials for our frontend requests; keeping this false avoids
    # invalid CORS combinations (credentials + wildcard origin) that can show up as
    # generic "Network Error" in the browser.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers defensively so one failing import won't crash the whole function.
def _include_router_safe(module_path: str, prefix: str, tags: list[str]) -> None:
    try:
        module = importlib.import_module(module_path)
        app.include_router(module.router, prefix=prefix, tags=tags)
        logger.info(f"Loaded router: {module_path}")
    except Exception as e:
        logger.exception(f"Failed loading router {module_path}: {e}")


_include_router_safe("app.api.chat", "/api/chat", ["chat"])
_include_router_safe("app.api.upload", "/api/upload", ["upload"])
_include_router_safe("app.api.knowledge", "/api/knowledge", ["knowledge"])

@app.get("/")
async def root():
    return {
        "message": "Personal Knowledge Agent API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
