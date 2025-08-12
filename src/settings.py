from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
import os

# nájde .env od aktuálneho CWD smerom hore (git root atď.)
dotenv_path = find_dotenv(usecwd=True)
load_dotenv(dotenv_path)

class Settings(BaseModel):
    meraki_api_key: str = os.getenv("MERAKI_API_KEY", "")
    meraki_org_id: str = os.getenv("MERAKI_ORG_ID", "")
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama")
    llm_model: str = os.getenv("LLM_MODEL", "llama3.2:latest")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    serpapi_api_key: str = os.getenv("SERPAPI_API_KEY", "")
    teams_webhook_url: str = os.getenv("TEAMS_WEBHOOK_URL", "")
    db_path: str = os.getenv("DB_PATH", "data.sqlite3")

if os.getenv("DEBUG") == "1":
    print(f"[settings] .env: {dotenv_path!r} exists={os.path.exists(dotenv_path)}", flush=True)
    print(f"[settings] KEY_SET={bool(os.getenv('MERAKI_API_KEY'))} ORG={os.getenv('MERAKI_ORG_ID')}", flush=True)

settings = Settings()