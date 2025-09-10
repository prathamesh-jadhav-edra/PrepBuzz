"""Configuration management for PrepBuzz CAT Questions RAG System."""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config(BaseSettings):
    """Application configuration."""

    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")

    # Google Search Configuration
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    google_cse_id: Optional[str] = Field(default=None, env="GOOGLE_CSE_ID")

    # Qdrant Configuration
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")

    # Application Settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    max_questions_per_run: int = Field(default=1, env="MAX_QUESTIONS_PER_RUN")
    output_dir: str = Field(default="./output", env="OUTPUT_DIR")

    # Project paths
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent
    )
    data_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent / "data"
    )

    @property
    def has_paid_llm(self) -> bool:
        """Check if any paid LLM API keys are available."""
        return bool(self.openai_api_key or self.anthropic_api_key)

    @property
    def sqlite_path(self) -> Path:
        """Path to SQLite database."""
        return self.data_dir / "cat_questions.db"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global config instance
config = Config()
