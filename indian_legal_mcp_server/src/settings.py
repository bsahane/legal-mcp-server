from functools import cached_property
from typing import List, Literal, Optional

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

from indian_legal_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()

try:
    load_dotenv()
except Exception as e:
    logger.warning(f"Could not load .env file: {e}")


def parse_sso_scopes(sso_scopes: str) -> list[str]:
    raw = sso_scopes or ""
    return [s.strip() for s in raw.split(",") if s.strip()]


def validate_sso_scopes(enable_auth: bool, sso_scopes: str) -> None:
    if enable_auth and not parse_sso_scopes(sso_scopes):
        raise ValueError(
            "SSO_SCOPES must contain at least one OAuth scope when ENABLE_AUTH is True "
            '(comma-separated, e.g. "email,openid,profile").'
        )


class Settings(BaseSettings):
    # MCP Server Configuration
    MCP_HOST: str = Field(
        default="localhost",
        json_schema_extra={
            "env": "MCP_HOST",
            "description": "Host address for the MCP server",
            "example": "localhost",
        },
    )
    MCP_PORT: int = Field(
        default=5001,
        ge=1024,
        le=65535,
        json_schema_extra={
            "env": "MCP_PORT",
            "description": "Port number for the MCP server",
            "example": 5001,
        },
    )
    MCP_SSL_KEYFILE: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "env": "MCP_SSL_KEYFILE",
            "description": "Path to SSL private key file for HTTPS",
            "example": "/path/to/key.pem",
        },
    )
    MCP_SSL_CERTFILE: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "env": "MCP_SSL_CERTFILE",
            "description": "Path to SSL certificate file for HTTPS",
            "example": "/path/to/cert.pem",
        },
    )
    MCP_TRANSPORT_PROTOCOL: str = Field(
        default="http",
        json_schema_extra={
            "env": "MCP_TRANSPORT_PROTOCOL",
            "description": "Transport protocol for the MCP server",
            "example": "streamable-http",
            "enum": ["streamable-http", "sse", "http"],
        },
    )
    PYTHON_LOG_LEVEL: str = Field(
        default="INFO",
        json_schema_extra={
            "env": "PYTHON_LOG_LEVEL",
            "description": "Logging level for the application",
            "example": "INFO",
            "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        },
    )
    CORS_ENABLED: bool = Field(
        default=False,
        json_schema_extra={
            "env": "CORS_ENABLED",
            "description": "Enable CORS for the MCP server",
            "example": True,
        },
    )
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        json_schema_extra={
            "env": "CORS_ORIGINS",
            "description": "Origins allowed to access the MCP server",
            "example": ["*"],
        },
    )
    CORS_CREDENTIALS: bool = Field(
        default=True,
        json_schema_extra={
            "env": "CORS_CREDENTIALS",
            "description": "Allow credentials for CORS requests",
            "example": True,
        },
    )
    CORS_METHODS: List[str] = Field(
        default=["*"],
        json_schema_extra={
            "env": "CORS_METHODS",
            "description": "Methods allowed for CORS requests",
            "example": ["*"],
        },
    )
    CORS_HEADERS: List[str] = Field(
        default=["*"],
        json_schema_extra={
            "env": "CORS_HEADERS",
            "description": "Headers allowed for CORS requests",
            "example": ["*"],
        },
    )

    # SSO / OAuth Configuration
    SSO_CLIENT_ID: str = Field(
        default="",
        json_schema_extra={
            "env": "SSO_CLIENT_ID",
            "description": "Client ID for the SSO",
            "example": "1234567890",
        },
    )
    SSO_CLIENT_SECRET: str = Field(
        default="",
        json_schema_extra={
            "env": "SSO_CLIENT_SECRET",
            "description": "Client secret for the SSO",
            "example": "1234567890",
        },
    )
    SSO_CALLBACK_URL: str = Field(
        default="",
        json_schema_extra={
            "env": "SSO_CALLBACK_URL",
            "description": "Callback URL for the SSO",
            "example": "http://localhost:3000/auth/callback",
        },
    )
    SSO_AUTHORIZATION_URL: str = Field(
        default="",
        json_schema_extra={
            "env": "SSO_AUTHORIZATION_URL",
            "description": "SSO authorization endpoint URL",
        },
    )
    SSO_TOKEN_URL: str = Field(
        default="",
        json_schema_extra={
            "env": "SSO_TOKEN_URL",
            "description": "SSO token endpoint URL",
        },
    )
    SSO_INTROSPECTION_URL: str = Field(
        default="",
        json_schema_extra={
            "env": "SSO_INTROSPECTION_URL",
            "description": "SSO token introspection endpoint URL",
        },
    )
    SSO_INTROSPECTION_MODE: Literal["rfc7662", "tokeninfo"] = Field(
        default="rfc7662",
        json_schema_extra={
            "env": "SSO_INTROSPECTION_MODE",
            "description": (
                "Token validation strategy: rfc7662 (POST introspection) or "
                "tokeninfo (GET access_token query param for providers like Google)"
            ),
            "example": "rfc7662",
            "enum": ["rfc7662", "tokeninfo"],
        },
    )
    SSO_SCOPES: str = Field(
        default="email,openid,profile,session:role-any",
        json_schema_extra={
            "env": "SSO_SCOPES",
            "description": (
                "Comma-separated OAuth scopes to request (e.g. email,openid,profile for Google). "
                "When ENABLE_AUTH is True, at least one non-empty scope is required."
            ),
            "example": "email,openid,profile",
        },
    )
    SESSION_SECRET: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "env": "SESSION_SECRET",
            "description": "Secret key for session middleware (required in production)",
            "example": "your-super-secret-session-key-here",
            "sensitive": True,
        },
    )
    USE_EXTERNAL_BROWSER_AUTH: bool = Field(
        default=False,
        json_schema_extra={
            "env": "USE_EXTERNAL_BROWSER_AUTH",
            "description": "Whether the application is running in local development mode",
            "example": "true",
        },
    )
    MCP_HOST_ENDPOINT: str = Field(
        default="http://localhost:5001",
        json_schema_extra={
            "env": "MCP_HOST_ENDPOINT",
            "description": "Host endpoint for the MCP server",
            "example": "http://localhost:5001",
        },
    )
    ENVIRONMENT: str = Field(
        default="development",
        json_schema_extra={
            "env": "ENVIRONMENT",
            "description": "Environment for the MCP server",
            "example": "development",
        },
    )
    COMPATIBLE_WITH_CURSOR: bool = Field(
        default=False,
        json_schema_extra={
            "env": "COMPATIBLE_WITH_CURSOR",
            "description": "Whether the MCP server is compatible with Cursor OAuth2 flow",
            "example": True,
        },
    )
    ENABLE_AUTH: bool = Field(
        default=True,
        json_schema_extra={
            "env": "ENABLE_AUTH",
            "description": "Enable authentication for the MCP server",
            "example": "true",
        },
    )

    # PostgreSQL Configuration
    POSTGRES_HOST: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "env": "POSTGRES_HOST",
            "description": "PostgreSQL host address",
            "example": "localhost",
        },
    )
    POSTGRES_PORT: Optional[int] = Field(
        default=None,
        ge=1024,
        le=65535,
        json_schema_extra={
            "env": "POSTGRES_PORT",
            "description": "PostgreSQL port number",
            "example": 5432,
        },
    )
    POSTGRES_DB: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "env": "POSTGRES_DB",
            "description": "PostgreSQL database name",
            "example": "indian_legal_mcp_server",
        },
    )
    POSTGRES_USER: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "env": "POSTGRES_USER",
            "description": "PostgreSQL username",
            "example": "postgres",
        },
    )
    POSTGRES_PASSWORD: Optional[str] = Field(
        default=None,
        json_schema_extra={
            "env": "POSTGRES_PASSWORD",
            "description": "PostgreSQL password",
            "example": "secretpassword",
            "sensitive": True,
        },
    )
    POSTGRES_POOL_SIZE: int = Field(
        default=10,
        ge=1,
        le=100,
        json_schema_extra={
            "env": "POSTGRES_POOL_SIZE",
            "description": "PostgreSQL connection pool minimum size",
            "example": 10,
        },
    )
    POSTGRES_MAX_CONNECTIONS: int = Field(
        default=20,
        ge=1,
        le=200,
        json_schema_extra={
            "env": "POSTGRES_MAX_CONNECTIONS",
            "description": "PostgreSQL connection pool maximum size",
            "example": 20,
        },
    )

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

    @model_validator(mode="after")
    def validate_oauth_scopes(self) -> "Settings":
        validate_sso_scopes(self.ENABLE_AUTH, self.SSO_SCOPES)
        return self

    @cached_property
    def oauth_scopes(self) -> list[str]:
        return parse_sso_scopes(self.SSO_SCOPES)


def validate_config(settings: Settings) -> None:
    if not (1024 <= settings.MCP_PORT <= 65535):
        raise ValueError(
            f"MCP_PORT must be between 1024 and 65535, got {settings.MCP_PORT}"
        )

    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if settings.PYTHON_LOG_LEVEL.upper() not in valid_log_levels:
        raise ValueError(
            f"PYTHON_LOG_LEVEL must be one of {valid_log_levels}, got {settings.PYTHON_LOG_LEVEL}"
        )

    valid_transport_protocols = ["streamable-http", "sse", "http"]
    if settings.MCP_TRANSPORT_PROTOCOL not in valid_transport_protocols:
        raise ValueError(
            f"MCP_TRANSPORT_PROTOCOL must be one of {valid_transport_protocols}, got {settings.MCP_TRANSPORT_PROTOCOL}"
        )

    validate_sso_scopes(settings.ENABLE_AUTH, settings.SSO_SCOPES)


settings = Settings()
