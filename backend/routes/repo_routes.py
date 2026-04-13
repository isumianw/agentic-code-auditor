from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.repo_service import clone_repository, delete_repository

# mini FastAPI app to group related routes together
# then this is plugged into main.py

router = APIRouter(
    prefix="/repo", # all routes here start with /repo
    tags=["Repository"] # groups them nicely in the /docs page
)

# REQUEST/RESPONSE MODELS
class CloneRequest(BaseModel):
    github_url: str # the only thing taken from the user

    class Config:
        json_schema_extra = {
            "example": {
                "github_url": "https://github.com/username/some-repo"
            }
        }

class CloneResponse(BaseModel):
    success: bool
    repo_name: str | None
    local_path: str | None
    message: str

class DeleteRequest(BaseModel):
    repo_name: str

# ENDPOINTS
@router.post("/clone", response_model=CloneResponse)
def clone_repo(request: CloneRequest):
    """
    accepts GitHub URL and clones the repository locally
    this is the first step of the analysis pipeline
    """
    result = clone_repository(request.github_url)
    return CloneResponse(**result)

@router.delete("/delete")
def delete_repo(request: DeleteRequest):
    """
    deletes a previously cloned repository from temp storage
    """
    result = delete_repository(request.repo_name)
    return result

@router.get("/status/{repo_name}")
def check_repo_status(repo_name: str):
    """
    checks whether a specific repo has already been cloned locally
    """
    import os
    local_path = f"temp_repos/{repo_name}"
    exists = os.path.exists(local_path)

    return {
        "repo_name": repo_name,
        "is_cloned": exists,
        "local_path": local_path if exists else None
    }