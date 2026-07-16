from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # LLM Configuration
    LLM_PROVIDER: str = "anthropic"
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    LLM_FALLBACK_PROVIDER: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # External API Keys
    ECOURTS_API_KEY: Optional[str] = None
    ECOURTS_PROVIDER: str = "ecourts_india"
    INDIANKANOON_API_TOKEN: Optional[str] = None

    # Feature Flags
    ENABLE_LLM_TOOLS: bool = True
    ENABLE_EXTERNAL_APIS: bool = True
    DEFAULT_LANGUAGE: str = "en"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 30
    RATE_LIMIT_LLM_PER_MINUTE: int = 10
    RATE_LIMIT_EXTERNAL_API_PER_MINUTE: int = 20

    # Privacy
    LOG_PII: bool = False
    REDACT_SCENARIO_INPUT: bool = True

    # Data
    STATUTE_INDEX_PATH: str = "indian_legal_mcp_server/data/statute_index.db"
    DATA_DIR: str = "indian_legal_mcp_server/data"

    # Timeouts (seconds)
    EXTERNAL_API_TIMEOUT: int = 10
    LLM_CALL_TIMEOUT: int = 30
    TOTAL_ORCHESTRATION_TIMEOUT: int = 60

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
