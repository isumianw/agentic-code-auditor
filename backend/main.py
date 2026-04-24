from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.repo_routes import router as repo_router
from backend.routes.scanner_routes import router as scanner_router

# FastAPI app instance
app = FastAPI(
    title="Agentic Code Auditor",
    description="An agentic AI system that autonomously audits GitHub repositories by combining static analysis tools and LLM reasoning to detect bugs, security vulnerabilities, and performance issues and generate actionable fixes like a senior software engineer.",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register routers
# prefix="/api/v1" (all routes become /api/v1/repo/clone etc.)
app.include_router(repo_router, prefix="/api/v1")
app.include_router(scanner_router, prefix="/api/v1")

# health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "running",
        "message": "Agentic Code Auditor API is live",
        "version": "0.1.0"
    }

# root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to Agentic Code Auditor",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "clone_repo":       "POST /api/v1/repo/clone",
            "delete_repo":      "DELETE /api/v1/repo/delete",
            "repo_status":      "GET /api/v1/repo/status/{repo_name}",
            "scan_repo":        "POST /api/v1/scanner/scan",
            "scan_summary":     "POST /api/v1/scanner/scan/summary",
            "list_files":       "GET /api/v1/scanner/list/{repo_name}",
            "get_single_file":  "POST /api/v1/scanner/file"
        }
    }