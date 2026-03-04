from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "PROTOCLAW_"}

    # Database
    database_url: str = (
        "postgresql+asyncpg://protoclaw:protoclaw@localhost:5432/protoclaw"
    )

    # Google Cloud
    gcp_project: str = ""
    gcp_location: str = "us-central1"
    gcs_bucket: str = "protoclaw-artifacts"

    # LLM — GLM-5 via Vertex AI Model Garden
    vertex_model: str = "zai-org/glm-5"

    # Confidence thresholds
    auto_publish_threshold: float = 0.85
    review_required_threshold: float = 0.60

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
