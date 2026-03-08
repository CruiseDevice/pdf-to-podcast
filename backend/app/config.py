from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PDF to Podcast"
    database_url: str = "sqlite:///./pdfpodcast.db"
    groq_api_key: str = ""
    upload_dir: str = "./uploads"
    audio_dir: str = "./audio"
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"


settings = Settings()
