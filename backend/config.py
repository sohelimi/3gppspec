from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    groq_api_key: str
    gemini_api_key: str = ""  # kept for reference, not used
    specs_dir: str = "/Users/sohel/3gpp_specs_2024_09"
    chroma_db_path: str = "./data/chromadb"
    ingest_releases: str = "Rel-17,Rel-18,Rel-19"
    ingest_series: str = "23_series,24_series,33_series,38_series"
    app_env: str = "development"
    allowed_origins: str = "http://localhost:3000"

    @property
    def releases(self) -> list[str]:
        return [r.strip() for r in self.ingest_releases.split(",")]

    @property
    def series(self) -> list[str]:
        return [s.strip() for s in self.ingest_series.split(",")]

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
