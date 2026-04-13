import os
import shutil
import stat
import re
from git import Repo, GitCommandError

# folder where we temporarily store cloned repos
TEMP_REPOS_DIR = "temp_repos"

def validate_github_url(url: str) -> bool:
    """
    checks if the URL is actually a valid GitHub repo URL
    to avoid people sending random URLs to the API

    valid URLs should be like this:
    https://github.com/username/repo
    https://github.com/username/repo.git
    """
    url = url.strip()
    
    # remove ".git" from the end
    if url.endswith(".git"):
        url = url[:-4]
    
    # regex pattern
    pattern = r'^https://github\.com/[\w\-]+/[\w\-\.]+/?$'

    return bool(re.match(pattern, url))

def get_repo_name_from_url(url: str) -> str:
    """
    extracts just the repo name from the URL

    say the URL is this:
    https://github.com/username/my-project

    then the repo name is: my-project
    """
    url = url.strip()

    # remove the slash at the end first
    if url.endswith('/'):
        url = url[:-1]

    # remove .git
    if url.endswith('.git'):
        url = url[:-4]
    
    return url.split('/')[-1]

def clone_repository(github_url: str) -> dict:
    """
    main function - takes a GitHub URL, clones it, returns info about it

    this function returns a dict with:
        1. success (True/False)
        2. local_path (where it was cloned to)
        3. repo_name
        4. message
    """
    # first validate the URL
    if not validate_github_url(github_url):
        return {
            "success": False,
            "local_path": None,
            "repo_name": None,
            "message": "Invalid GitHub URL. Please use format: https://github.com/username/repo"
        }
    
    # next get the repo name from the URL
    repo_name = get_repo_name_from_url(github_url)

    # build the full local path where the repo will be cloned to
    local_path = os.path.join(TEMP_REPOS_DIR, repo_name)

    # in case if this repo was cloned before then delete it and re-clone
    # this is to make sure that the latest version is available
    if os.path.exists(local_path):
        shutil.rmtree(local_path)
        print(f"Deleted existing clone at: {local_path}")
    
    # next make sure the temp_repos folder exists
    os.makedirs(TEMP_REPOS_DIR, exist_ok=True)

    # now actually clone the repo
    try:
        print(f"Cloning {github_url} into {local_path}...")
        Repo.clone_from(github_url, local_path)
        print(f"Clone successful!")
        return {
            "success": True,
            "local_path": local_path,
            "repo_name": repo_name,
            "message": f"Successfully cloned '{repo_name}'"
        }
    
    except GitCommandError as e:
        # this catches errors from git itself (like if repo doesn't exist, private repo)
        return {
            "success": False,
            "local_path": None,
            "repo_name": None,
            "message": f"Git error: {str(e)}"
        }
    
    except Exception as e:
        # catch any other unexpected errors
        return {
            "success": False,
            "local_path": None,
            "repo_name": None,
            "message": f"Unexpected error: {str(e)}"
        }

def handle_remove_readonly(func, path, exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)
    
def delete_repository(repo_name: str) -> dict:
    """
    deletes a cloned repo from temp storage to free up space
    this will be used after analysis is done
    """
    local_path = os.path.join(TEMP_REPOS_DIR, repo_name)

    if not os.path.exists(local_path):
        return {
            "success": False,
            "message": f"Repo '{repo_name}' not found in temp storage"
        }

    try:
        shutil.rmtree(local_path, onerror=handle_remove_readonly)

        return {
            "success": True,
            "message": f"Deleted '{repo_name}' from temp storage"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Delete failed: {str(e)}"
        }