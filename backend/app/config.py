from functools import lru_cache
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    app_name: str = "UBID System"
    database_url: str = Field(
        default=os.getenv("DATABASE_URL", "postgresql://ubid:ubid_secret@localhost:5432/ubid")
    )
    secret_key: str = Field(default=os.getenv("SECRET_KEY", "local-dev-secret"))
    frontend_origin: str = Field(default=os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"))
    page_limit_default: int = 20
    search_limit: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
