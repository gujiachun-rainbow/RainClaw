"""Task service configuration."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API
    api_host: str = os.environ.get("TASK_API_HOST", "0.0.0.0")
    api_port: int = int(os.environ.get("TASK_API_PORT", "8001"))

    # 展示用时间（下次执行、执行记录等）的时区，默认北京时间
    display_timezone: str = os.environ.get("DISPLAY_TIMEZONE", "Asia/Shanghai")

    # MongoDB (same as main backend or dedicated)
    mongodb_host: str = os.environ.get("MONGODB_HOST", "localhost")
    mongodb_port: int = int(os.environ.get("MONGODB_PORT", "27014"))
    mongodb_db_name: str = os.environ.get("MONGODB_DB", "ai_agent")
    mongodb_username: str = os.environ.get("MONGODB_USER", "")
    mongodb_password: str = os.environ.get("MONGODB_PASSWORD", "")

    # Redis (Celery broker)
    redis_url: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Chat service (main backend) - for task execution
    chat_service_url: str = os.environ.get("CHAT_SERVICE_URL", "http://backend:8000")
    chat_service_api_key: str = os.environ.get("CHAT_SERVICE_API_KEY", "")

    # LLM for natural language -> crontab (optional, can use chat service)
    llm_api_key: str = os.environ.get("DS_API_KEY", "")
    llm_base_url: str = os.environ.get("DS_URL", "https://api.deepseek.com/v1")
    llm_model: str = os.environ.get("DS_MODEL", "deepseek-chat")


settings = Settings()
