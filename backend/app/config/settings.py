from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]
_load_env_file(REPO_ROOT / ".env")
_load_env_file(REPO_ROOT / ".env.local")
_load_env_file(BACKEND_ROOT / ".env")


def _as_float(value: str | None, fallback: float) -> float:
    if value is None or value == "":
        return fallback
    try:
        return float(value)
    except ValueError:
        return fallback


def _as_int(value: str | None, fallback: int) -> int:
    if value is None or value == "":
        return fallback
    try:
        return int(float(value))
    except ValueError:
        return fallback


def _split_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "EAC Weekly Timesheet Classification API")
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BACKEND_ROOT / 'eac.db').as_posix()}"
    )
    rule_version: str = os.getenv("RULE_VERSION", "fixed-asset-policy-v1.0")
    persona_name: str = os.getenv("PERSONA_NAME", "Project Coder Weekly Timesheet")
    review_threshold: int = _as_int(os.getenv("REVIEW_THRESHOLD"), 70)
    semantic_store_label: str = os.getenv("SEMANTIC_STORE_LABEL", "pgvector")
    decision_authority_label: str = os.getenv(
        "DECISION_AUTHORITY_LABEL",
        "Policy-led deterministic rules"
    )
    llm_skip_threshold: int = _as_int(os.getenv("LLM_SKIP_THRESHOLD"), 85)
    llm_concurrency: int = _as_int(os.getenv("LLM_CONCURRENCY"), 20)
    llm_chunk_size: int = _as_int(os.getenv("LLM_CHUNK_SIZE"), 100)
    llm_batch_size: int = _as_int(os.getenv("LLM_BATCH_SIZE"), 10)
    llm_provider: str = os.getenv("LLM_PROVIDER", "azure_openai")
    llm_api_base_url: str = os.getenv("LLM_API_BASE_URL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_api_version: str = os.getenv("LLM_API_VERSION", "2024-02-15-preview")
    llm_temperature: float = _as_float(os.getenv("LLM_TEMPERATURE"), 0.1)
    llm_max_tokens: int = _as_int(os.getenv("LLM_MAX_TOKENS"), 500)
    llm_timeout_seconds: int = _as_int(os.getenv("LLM_TIMEOUT_SECONDS"), 30)
    cors_origins: tuple[str, ...] = _split_csv(
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
    )
    batch_window_hours: int = _as_int(os.getenv("BATCH_WINDOW_HOURS"), 24)
    ingestion_job_poll_seconds: int = _as_int(os.getenv("INGESTION_JOB_POLL_SECONDS"), 2)
    ingestion_job_ttl_seconds: int = _as_int(os.getenv("INGESTION_JOB_TTL_SECONDS"), 86400)
    ingestion_staging_dir: str = os.getenv(
        "INGESTION_STAGING_DIR",
        str(BACKEND_ROOT / "tmp" / "ingestion_jobs")
    )
    extraction_confidence_floor: float = _as_float(
        os.getenv("EXTRACTION_CONFIDENCE_FLOOR"),
        0.9
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
