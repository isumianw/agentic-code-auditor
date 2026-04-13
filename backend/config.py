import os
from dotenv import load_dotenv

# load the .env file
load_dotenv()

# app settings in one place
class Settings:
    APP_NAME: str = "Agentic Code Auditor"
    VERSION: str = "0.2.0"
    TEMP_REPOS_DIR: str = "temp_repos"

    # Ai API keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # max repo size to prevent abuse (in MB)
    MAX_REPO_SIZE_MB: int = 100

settings = Settings()