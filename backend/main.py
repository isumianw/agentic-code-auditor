from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
        "health": "/health"
    }