from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.analyzers.file_scanner import scan_repository, get_file_by_path
import os

router = APIRouter(
    prefix="/scanner",
    tags=["Scanner"]
)

# REQUEST MODELS

class ScanRequest(BaseModel):
    repo_name: str # just the repo name not the full path

    class Config:
        json_schema_extra = {
            "example": {
                "repo_name": "flask"
            }
        }

class FileRequest(BaseModel):
    repo_name: str
    file_path: str # relative path inside the repo

    class Config:
        json_schema_extra = {
            "example": {
                "repo_name": "flask",
                "file_path": "src/app.py"
            }
        }

# ENDPOINTS

@router.post("/scan")
def scan_repo(request: ScanRequest):
    """
    scans a previously cloned repository and returns all file data
    you must clone the repo first using /api/v1/repo/clone
    """        
    local_path = os.path.join("temp_repos", request.repo_name)

    # check the repo exists before trying to scan it
    if not os.path.exists(local_path):
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{request.repo_name}' not found. Clone it first using /api/v1/repo/clone"
        )
    
    result = scan_repository(local_path)

    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result.get("errors", ["Unknown scan error"])
        )
    
    return result

@router.post("/scan/summary")
def scan_repo_summary(request: ScanRequest):
    """
    returns only the summary -  no file contents
    useful when you want a quick overview without the full data
    """
    local_path = os.path.join("temp_repos", request.repo_name)

    if not os.path.exists(local_path):
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{request.repo_name}' not found."
        )
    
    result = scan_repository(local_path)

    # return summary and file list without content
    files_without_content = []
    for f in result.get("files", []):
        file_info = {k: v for k, v in f.items() if k != "content"}
        files_without_content.append(file_info)
    
    return {
        "success": result["success"],
        "repo_path": result["repo_path"],
        "summary": result["summary"],
        "files": files_without_content,
        "errors": result["errors"]
    }

@router.post("/file")
def get_single_file(request: FileRequest):
    """
    returns data for a single specific file in the repo
    """
    local_path = os.path.join("temp_repos", request.repo_name)

    if not os.path.exists(local_path):
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{request.repo_name}' not found."
        )
    
    result = get_file_by_path(local_path, request.file_path)

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "File not found")
        )
    
    return result

@router.get("/list/{repo_name}")
def list_scanned_files(repo_name: str):
    """
    quickly lists all Python files in a repo without reading their content
    """
    local_path = os.path.join("temp_repos", repo_name)

    if not os.path.exists(local_path):
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{repo_name}' not found."
        )
    
    python_files = []

    for root, dirs, files in os.walk(local_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'venv', 'node_modules'}]

        for file_name in files:
            if file_name.endswith('.py'):
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, local_path).replace('\\', '/')
                size_kb = round(os.path.getsize(file_path) / 1024, 2)

                python_files.append({
                    "file_name": file_name,
                    "relative_path": relative_path,
                    "size_kb": size_kb
                })
    
    return {
        "repo_name": repo_name,
        "total_python_files": len(python_files),
        "files": python_files
    }